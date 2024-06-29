import datetime
import urllib

import puz
from puz import DefaultClueNumbering
import requests

from .basedownloader import BaseDownloader
from util import *

class NewYorkTimesSyndicatedDownloader(BaseDownloader):
    command = 'nyts'
    outlet = 'New York Times Syndicated'
    outlet_prefix = 'NY Times Syndicated'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.url_from_id = 'https://nytsyn.pzzl.com/nytsyn-crossword-mh/nytsyncrossword?date={}'

        self.headers = {}
        self.cookies = {}

    def find_latest(self):
        dt = datetime.datetime.today()
        return self.find_by_date(dt)

    def find_by_date(self, dt):
         formatted_date = dt.strftime('%y%m%d')
         self.date = dt
         return self.url_from_id.format(formatted_date)

    def find_solver(self, url):
        return url

    def fetch_data(self, solver_url):
        res = requests.get(solver_url, cookies=self.cookies)
        res.raise_for_status()

        return res.text

    def parse_xword(self, xword_data):
        sections = ['note', 'title', 'authors', 'width', 'height', 'ignore', 'ignore', 'grid', 'across_clues', 'down_clues']
        puzzle = puz.Puzzle()

        lines = xword_data.split('\n')[2:]

        fill = ''
        solution = ''
        clues = []
        rebus_board = []
        rebus_index = 0
        rebus_table = ''
        markup = b''

        for line in lines:
            if (len(sections) == 0):
                break
            if (line.strip() == ''):
                sections.pop(0)
                continue

            section = sections[0]

            if (section == 'note'):
                original_date = datetime.datetime.strptime(line.strip(), '%y%m%d')
                puzzle.notes = original_date.strftime('%A, %B %d, %Y')
            elif (section == 'title'):
                puzzle.title = line.strip()
            elif (section == 'authors'):
                puzzle.author = line.strip()
            elif (section == 'width'):
                puzzle.width = int(line.strip())
            elif (section == 'height'):
                puzzle.height = int(line.strip())
            elif (section == 'grid'):
                row = line.strip()
                i = 0
                while i < len(row):
                    if (row[i] == '#' or row[i] == '.'):
                        fill += '.'
                        solution += '.'
                        markup += b'\x00'
                        rebus_board.append(0)
                    elif (row[i] == '%'):
                        # circled cell
                        markup += b'\x80'
                    elif (row[i] == '^'):
                        # shaded cell, using 'hinted cell'
                        markup += b'\x40'
                    elif (i + 1 < len(row) and row[i+1] == ','):
                        # rebus is formatted as letters with commas between the word
                        fill += '-'
                        solution += row[i]
                        markup += b'\x00'

                        rebus_word = ''
                        while True:
                            if (row[i] == ','):
                                i += 1
                                continue
                            else:
                                rebus_word += row[i]
                                i += 1
                                if (i >= len(row) or row[i] != ','):
                                    break
                        rebus_board.append(rebus_index + 1)
                        rebus_table += '{:2d}:{};'.format(rebus_index, rebus_word)
                        rebus_index += 1
                        continue
                    else:
                        fill += '-'
                        solution += row[i]
                        rebus_board.append(0)
                        if (i == 0 or (row[i-1] != '%' and row[i-1] != '^')):
                            markup += b'\x00'
                    i+=1
            elif (section == 'across_clues'):
                clues.append({'value': line.strip(), 'direction': 'A', 'num': 0})
            elif (section == 'down_clues'):
                clues.append({'value': line.strip(), 'direction': 'D', 'num': 0})


        puzzle.fill = fill
        puzzle.solution = solution
        numbering = DefaultClueNumbering(puzzle.fill, ["temp-value" for c in clues], puzzle.width, puzzle.height)
        i = 0
        for mapping in numbering.across:
            clues[i]['num'] = mapping['num']
            i+=1

        for mapping in numbering.down:
            clues[i]['num'] = mapping['num']
            i+=1
        clues.sort(key=lambda c: (int(c['num']), c['direction']))
        puzzle.clues = [c['value'] for c in clues]

        if (b'\x80' in markup or b'\x40' in markup):
            puzzle.extensions[b'GEXT'] = markup
            puzzle._extensions_order.append(b'GEXT')
            puzzle.markup()

        if any(rebus_board):
            puzzle.extensions[b'GRBS'] = bytes(rebus_board)
            puzzle.extensions[b'RTBL'] = rebus_table.encode(puz.ENCODING)
            puzzle._extensions_order.extend([b'GRBS', b'RTBL'])
            puzzle.rebus()

        return puzzle