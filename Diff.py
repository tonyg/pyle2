import os
import re

markerre = re.compile(r'^@@ -(\d+)(,\d+)? \+(\d+)(,\d+)? @@')

class Chunk:
    def __init__(self, linenumber1, linenumber2):
        self.linenumber1 = linenumber1
        self.linenumber2 = linenumber2
        self.header = []
        self.footer = []
        self.chunk1 = []
        self.chunk2 = []
        self.state = 0
        self.kind = None

    def extend(self, discriminator, line):
        if discriminator == ' ':
            if self.state == 0:
                self.header.append(line)
            else:
                self.state = 2
                self.footer.append(line)
        elif discriminator == '-':
            if self.state == 2:
                return True
            self.state = 1
            self.chunk1.append(line)
        elif discriminator == '+':
            if self.state == 2:
                return True
            self.state = 1
            self.chunk2.append(line)
        else:
            pass
        return False

    def finish(self):
        if self.chunk1 and self.chunk2:
            self.kind = 'change'
        elif self.chunk1:
            self.kind = 'deletion'
        elif self.chunk2:
            self.kind = 'insertion'
        else:
            self.kind = 'nothing'

    def reverse(self):
        t = self.chunk1
        self.chunk1 = self.chunk2
        self.chunk2 = t
        t = self.linenumber1
        self.linenumber1 = self.linenumber2
        self.linenumber2 = t
        self.finish()

class Diff:
    def __init__(self, title, v1, v2, difflines):
        self.title = title
        self.v1 = v1
        self.v2 = v2
        self.chunks = []
        self.chunk = None
        self.parse_result(difflines)

    def finish_chunk(self):
        if self.chunk:
            self.chunk.finish()
            self.chunks.append(self.chunk)
            self.chunk = None

    def parse_result(self, result):
        for line in result:
            markermatch = markerre.search(line)
            if markermatch:
                self.finish_chunk()
                self.chunk = Chunk(markermatch.group(1), markermatch.group(3))
            elif self.chunk:
                if self.chunk.extend(line[0], line[1:]):
                    self.finish_chunk()
                    self.chunk = Chunk(None, None)
                    self.chunk.extend(line[0], line[1:])
        self.finish_chunk()

    def reverse(self):
        t = self.v1
        self.v1 = self.v2
        self.v2 = t
        for chunk in self.chunks:
            chunk.reverse()
