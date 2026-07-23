import collections

class peek_ahead:
    """Iterator that can look ahead one step

    From example 16.7 from python cookbook 2.

    The preview can be inspected through it.preview

    ignoring duplicates:
    >>> it = peek_ahead('122345567')
    >>> for i in it:
    ...     if it.preview == i:
    ...         continue
    ...     print(i, end=' ')
    1 2 3 4 5 6 7

    getting duplicates together:
    >>> it = peek_ahead('abbcdddde')
    >>> for i in it:
    ...     if it.preview == i:
    ...         dup = 1
    ...         while 1:
    ...             i = it.next()
    ...             dup += 1
    ...             if i != it.preview:
    ...                 print(i*dup, end='')
    ...                 break
    ...     else:
    ...         print(i, end='')
    ...
    a bb c dddd e

    """
    sentinel = object() #schildwacht
    def __init__(self, it):
        self._nit = iter(it).__next__
        self.preview = None
        self._step()
    def __iter__(self):
        return self
    def __next__(self):
        result = self._step()
        if result is self.sentinel:
            raise StopIteration
        return result
    def _step(self):
        result = self.preview
        try:
            self.preview = self._nit()
        except StopIteration:
            self.preview = self.sentinel
        return result

# class peek_ahead_stripped(peek_ahead):
#     """ Iterator that strips the lines of text, and returns (leftSpaces,strippedLine)
# 
#     sentinel is just False, such that peeking ahead can check for truth input
# 
#     >>> lines = '\\n'.join(['line1', '', ' one space ahead','', '   three spaces ahead, 1 empty line before'])
#     >>> import StringIO
#     >>> list(peek_ahead_stripped(StringIO.StringIO(lines)))
#     [(0, 'line1'), (0, ''), (1, 'one space ahead'), (0, ''), (3, 'three spaces ahead, 1 empty line before')]
# 
#     example of testing look ahead
# 
#     >>> lines = '\\n'.join(['line1', '', 'line2 (last)'])
#     >>> it = peek_ahead_stripped(StringIO.StringIO(lines))
#     >>> for spaces, text in it:
#     ...     print('current line: |', text, '|',)
#     ...     if it.preview is it.sentinel:
#     ...         print(', cannot preview, end of peek_ahead_stripped')
#     ...     elif it.preview[1]:
#     ...         print(', non empty preview: |', it.preview[1], '|')
#     ...     else:
#     ...         print(', empty preview')
#     current line: | line1 | , empty preview
#     current line: |  | , non empty preview: | line2 (last) |
#     current line: | line2 (last) | , cannot preview, end of peek_ahead_stripped
# 
#     """
#     sentinel = peek_ahead.sentinel
#     
#     def __next__(self):
#         result = self._step()
#         if result is self.sentinel:
#             raise StopIteration
#         return result
#     
#     def _step(self):
#         """collect the line and do the processing"""
#         result = self.preview
#         try:
#             line = self._nit().rstrip()
#             self.preview = (len(line) - len(line.lstrip()), line.lstrip())
#         except StopIteration:
#             self.preview = self.sentinel
#         return result


class peekable:
    """ An iterator that supports a peek operation. 
    
    this is a merge of example 19.18 of python cookbook part 2, peek ahead more steps
    and the simpler example 16.7, which peeks ahead one step and stores it in
    the self.preview variable.
    
    Adapted so the peek function never raises an error, but gives the
    self.sentinel value in order to identify the exhaustion of the iter object.
    
    Example usage:
    
    >>> p = peekable(range(4))
    >>> p.peek()
    0
    >>> p.next(1)
    [0]
    >>> p.isFirst()
    True
    >>> p.preview
    1
    >>> p.isFirst()
    True
    >>> p.peek(3)
    [1, 2, 3]
    >>> p.next(2)
    [1, 2]
    >>> p.peek(2) #doctest: +ELLIPSIS
    [3, <object object at ...>]
    >>> p.peek(1)
    [3]
    >>> p.next(2)
    Traceback (most recent call last):
    StopIteration
    >>> p.next()
    3
    >>> p.isLast()
    True
    >>> p.next()
    Traceback (most recent call last):
    StopIteration
    >>> p.next(0)
    []
    >>> p.peek()  #doctest: +ELLIPSIS
    <object object at ...>
    >>> p.preview #doctest: +ELLIPSIS
    <object object at ...>
    >>> p.isLast()  # after the iter process p.isLast remains True
    True
    """
    sentinel = object() #schildwacht
    def __init__(self, iterable):
        self._nit = iter(iterable).__next__  # for speed
        self._iterable = iter(iterable)
        self._cache = collections.deque()
        self._fillcache(1)          # initialize the first preview already
        self.preview = self._cache[0]
        self.count = -1  # keeping the count, possible to check
                         # isFirst and isLast status
    def __iter__(self):
        return self
    def _fillcache(self, n):
        """fill _cache of items to come, with one extra for the preview variable
        """
        if n is None:
            n = 1
        while len(self._cache) < n+1:
            try:
                Next = self._nit()
            except StopIteration:
                # store sentinel, to identify end of iter:
                Next = self.sentinel
            self._cache.append(Next)
    def next(self, n=None):
        """gives next item of the iter, or a list of n items
        
        raises StopIteration if the iter is exhausted (self.sentinel is found),
        but in case of n > 1 keeps the iter alive for a smaller "next" calls
        """
        self._fillcache(n)
        if n is None:
            result = self._cache.popleft()
            if result == self.sentinel:
                # find sentinel, so end of iter:
                self.preview = self._cache[0]
                raise StopIteration
            self.count += 1
        else:
            result = [self._cache.popleft() for i in range(n)]
            if result and result[-1] == self.sentinel:
                # recache for future use:
                self._cache.clear()
                self._cache.extend(result)
                self.preview = self._cache[0]
                raise StopIteration
            self.count += n
        self.preview = self._cache[0]
        return result
    
    def isFirst(self):
        """returns true if iter is at first position
        """
        return self.count == 0

    def isLast(self):
        """returns true if iter is at last position or after StopIteration
        """
        return self.preview == self.sentinel
        
    def peek(self, n=None):
        """gives next item, without exhausting the iter, or a list of 0 or more next items
        
        with n == None, you can also use the self.preview variable, which is the first item
        to come.
        """
        self._fillcache(n)
        if n is None:
            result = self._cache[0]
        else:
            result = [self._cache[i] for i in range(n)]
        return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    