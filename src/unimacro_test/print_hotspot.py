#!/usr/bin/env python
#(re)test hotshot output (created with a unittest script)
# in use for unittestMessagefunctions.py (testing test_getting_more_info_from_application)...
import hotshot.stats
filePath = r'U:\messagesfunctionstest.prof'
stats = hotshot.stats.load(filePath)
stats.strip_dirs()
stats.sort_stats('cumulative', 'calls')
stats.print_stats()

