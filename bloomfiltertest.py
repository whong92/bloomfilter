import unittest
from bloomfilter import bloomFilterBasic, bloomFilter, scalableBloomFilter


class TestBloomFilterBasic(unittest.TestCase):

    """
    Tests the bloomFilterBasic class
    """

    def setUp(self):
        self.BF = bloomFilterBasic(n_bits = 30, n_hash = 3)

    def test_empty_filter(self):
        items = [56, 99.0, 'foo', 'bar', (1,2,3)]
        for item in items:
            self.assertFalse(self.BF.query_item(item))

    def test_insert_various(self):
        items = [56, 99.0, 'foo', 'bar', (1, 2, 3)]
        for item in items:
            self.BF.add_item(item)
            self.assertTrue(self.BF.query_item(item))

    def test_insert_int(self):
        ints = [56, 7, 1]
        for i in ints:
            self.BF.add_item(i)
            self.assertTrue(self.BF.query_item(i))

    def test_insert_float(self):
        floats = [5.6, 0.7, 100.1]
        for f in floats:
            self.BF.add_item(f)
            self.assertTrue(self.BF.query_item(f))

    def test_insert_str(self):
        strs = ['foo', 'bar', 'six']
        for s in strs:
            self.BF.add_item(s)
            self.assertTrue(self.BF.query_item(s))

    def test_insert_tups(self):
        tups = ['foo', 'bar', 'six']
        for t in tups:
            self.BF.add_item(t)
            self.assertTrue(self.BF.query_item(t))


class TestBloomFilter(TestBloomFilterBasic):
    """
    Extends the TestBloomFilterBasic to test the bloomFilter class
    """

    def setUp(self):
        self.BF = bloomFilter(cap=10, fpr=0.1)


class TestScalableBloomFilter(TestBloomFilterBasic):
    """
    Extends the TestBloomFilterBasic to test the scalableBloomFilter class
    """

    def setUp(self):
        self.BF = scalableBloomFilter(fpr=0.1)


class TestBloomFilterPerformance(unittest.TestCase):
    """
    Tests the performance of the bloomFilter class by inserting and testing for 10^5 ints. Tests it at various
    false positive rates
    """

    def setUp(self):
        self.fpr_expected = None

    def tearDown(self):
        """
        Run the test by inserting odd numbers between 0 and 2*(10^5)-1 and testing for false positives
        :return:
        """
        for i in range(200000):
            if i%2:
                # add odd numbers only
                self.BF.add_item(i)

        FP = 0
        for i in range(200000):
            if i%2:
                # all odd numbers must give positive test
                self.assertTrue(self.BF.query_item(i))
            else:
                # records false positives for even numbers
                if self.BF.query_item(i): FP += 1

        fpr = FP/100000
        print()
        print('expected FPR: {},  measured FPR: {} '.format(self.fpr_expected, fpr))

    def test_fpr_20_percent(self):
        self.fpr_expected = 0.2
        self.BF = bloomFilter(cap=100000, fpr=0.2)

    def test_fpr_10_percent(self):
        self.fpr_expected = 0.1
        self.BF = bloomFilter(cap=100000, fpr=0.1)

    def test_fpr_05_percent(self):
        self.fpr_expected = 0.05
        self.BF = bloomFilter(cap=100000, fpr=.05)

    def test_fpr_01_percent(self):
        self.fpr_expected = 0.01
        self.BF = bloomFilter(cap=100000, fpr=.01)


class TestScalableBloomFilterPerformance(TestBloomFilterPerformance):
    """
    Extends the TestBloomFilterPerformance to test performance of scalableBloomFilters. Tests it at various
    false positive rates
    """

    def test_fpr_20_percent(self):
        self.fpr_expected = 0.2
        self.BF = scalableBloomFilter(fpr=0.2)

    def test_fpr_10_percent(self):
        self.fpr_expected = 0.1
        self.BF = scalableBloomFilter(fpr=0.1)

    def test_fpr_05_percent(self):
        self.fpr_expected = 0.05
        self.BF = scalableBloomFilter(fpr=.05)

    def test_fpr_01_percent(self):
        self.fpr_expected = 0.01
        self.BF = scalableBloomFilter(fpr=.01)

        
if __name__ == '__main__':
    unittest.main()