from abc import ABC, abstractmethod
from bitarray import bitarray
import mmh3
import math


class bloomFilterBase(ABC):
    """
    Abstract Base Class for any bloomFilter definition
    Implementation of an add_item and query_item required
    Implementation must supports the insertion and query of any hashable data type (implements the __hash__() method)
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def add_item(self, item):
        """
        Abstract method to add item into the bloom filter. Required implementation by subclass
        :param item: Any hashable item
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def query_item(self, item):
        """
        Abstract method to query item from the bloom filter. Required implementation by subclass
        :param item: Any hashable item
        :return: boolean True/False
        """
        raise NotImplementedError


class bloomFilterBasic(bloomFilterBase):
    """
    Basic Bloom Filter Implementation as defined in https://en.wikipedia.org/wiki/Bloom_filter
    The number of bits, and number of hash functions need to be manually set for the basic bloom filter
    """

    def __init__(self, n_bits, n_hash):
        """
        Initialize the basic version of the bloom filter
        :param n_bits: Number of bits to allocate
        :param n_hash: Number of hash functions to use
        """
        assert n_bits > 0 and n_hash > 0 , \
            'Number of hashes and number of bits must be larger than 0! Expected number of items must be non-negative!'
        self.m = n_bits
        self.k = n_hash
        self.bit_array = bitarray(self.m)
        self.bit_array.setall(0)
        self.x = 0  # keep track of number of bits set to True

    def add_item(self, item):
        """
        Implementation of abstract method add_item
        :param item: Any hashable item
        :return: None
        """
        assert hasattr(item, '__hash__'), 'item must be hashable to be added to bloom filter!'
        for i in range(self.k):
            if not self.bit_array[self._compute_hash(item, i)]:
                self.bit_array[self._compute_hash(item, i)] = 1
                self.x += 1

    def query_item(self, item):
        """
        Implementation of abstract method query_item
        :param item: Any hashable item
        :return: boolean True/False
        """
        assert hasattr(item, '__hash__'), 'item must be hashable to query the bloom filter!'
        for i in range(self.k):
            if not self.bit_array[self._compute_hash(item, i)]:
                return False
        return True

    def _compute_hash(self, item, i):
        """
        Computes the position of item's i'th bit in the bitarray, using the i'th hash function
        :param item: Any hashable item
        :param i: Index of hash function
        :return: Position of i'th bit of item, using hash function i
        """
        return mmh3.hash(str(item.__hash__()), i) % self.m

    def approximate_num_items(self):
        return -(self.m / self.k) * math.log(1 - (self.x / self.m))


class bloomFilter(bloomFilterBasic):
    """
    Extension of the basic bloom filter. User specifies a capacity (estimated number of items to insert), and a desired false positive rate
    fpr. An optimal fill ratio of 0.5 at full capacity is assumed, and the optimal bitarray size m_opt and number of hash functions
    k_opt are calculated with respect to this.
    ref: https://en.wikipedia.org/wiki/Bloom_filter
    ref: http://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf
    """

    def __init__(self, cap, fpr):
        """
        Initializes a bloom filter with an intended capacity cap, and a desired false positive rate fpr
        :param cap: Intended capacity
        :param fpr: Desired false positive rate
        """
        assert 0 < fpr and fpr < 1, 'fpr needs to be a float that strictly in [0,1]!'
        assert cap > 0, 'capacity needs to be larger than 0!'
        self.p = fpr
        self.n = cap
        # allocate m_opt bits to accomodate estimated capacity and false positive ratio
        m_opt = - int(cap * math.log(fpr) / math.pow(math.log(2), 2))
        # allocate optimal k_opt
        k_opt = -int(math.log(fpr, 2))
        super().__init__(m_opt, k_opt)

    def is_at_capacity(self):
        """
        Uses the approximated number of items in the filter to test if the filter is at capacity
        :return: True if the approximate number of items in the filter is more than the intended capacity
        """
        if self.approximate_num_items() > self.n:
            return True
        return False


class scalableBloomFilter(bloomFilterBase):

    """
    Dynamic version of the bloom filter, as specified in http://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf
    The user defines a desired false positive ratio (fpr), and an initial capacity (cap0).

    Items are first added to the initial filter until it is at capacity. At this point when new items are added, a new
    filter with capacity s*cap0 is added, and new items added to the newest filter.

    To query items, every filter needs to be checked. Before adding a new item, query_filter is called to see if the
    filter returns true for the new item already. This way we can guard against expanding the filter unnecessarily.

    The constant s defines a growth rate of the filter capacity. The constant r scales the fpr of new filters so that
    the overall false positive rate remains bounded by the value supplied (fpr).
    """

    def __init__(self, fpr, cap0=128, s=2, r=.5):
        """
        Initializes the scalable bloom filter
        :param fpr: Desired false positive rate
        :param cap0: Initial capacity (default 128)
        :param s: Growth rate of filter sizes (must be larger than 1)
        :param r: Fpr multiplier (must be less than 1)
        """
        assert fpr < 1 and fpr > 0, 'False positive rate must be a number between 0 and 1!'
        assert cap0 > 0, 'Initial capacity must be larger than 0!'
        assert s > 1, 'Growth rate must be larger than 1!'
        assert r > 0 and r < 1, 'Fpr multiplier must be a number between 0 and 1!'
        super().__init__()
        self.cap_current = cap0
        self.fpr_current = fpr *r
        self.s = s
        self.r = r
        self.filters = [bloomFilter(self.cap_current, self.fpr_current)]

    def query_item(self, item):
        """
        Implementation of abstract method query_item. Checks every filter for item.
        :param item: Any hashable item
        :return: boolean True/False
        """
        for filter in self.filters:
            if filter.query_item(item):
                return True
        return False

    def add_item(self, item):
        """
        Implementation of abstract method add_item. Queries first before checking
        :param item: Any hashable item
        :return: None
        """
        if self.query_item(item):
            return

        if not self.filters[-1].is_at_capacity():
            self.filters[-1].add_item(item)
            return

        self.cap_current *= self.s
        self.fpr_current *= self.r
        self.filters.append(bloomFilter(self.cap_current, self.fpr_current))
        self.filters[-1].add_item(item)

        return


if __name__ == "__main__":

    """
    Script below demonstrates usage of bloomFilter and scalableBloomFilter classes
    Both classes implement a add_item and query_item method, which can take in any immutable (and hashable) data type
    """

    # Regular bloom filter
    BF = bloomFilter(cap=100, fpr=0.1)

    items_in_filter = ['hello', 'world', (9, 0, 0), 3, 66.6, -90.2]
    items_not_in_filter = ['goodbye', 'universe', (4, 0, 0), 1, -66.6, 90.2]

    print('Testing Bloom Filter')
    for item in items_in_filter:
        BF.add_item(item)

    print('\n Positive items')
    for item in items_in_filter:
        if not BF.query_item(item):
            print('Error! {} should be in the filter, but its not! '.format(item))
        else:
            print('{} is in the filter! '.format(item))

    print('\n Negative items')
    for item in items_not_in_filter:
        if BF.query_item(item):
            print('False positive on item {}! '.format(item))
        else:
            print('{} is not in the filter! '.format(item))
    print()


    # Dynamic bloom filter, only need to specify false positive rate
    BF = scalableBloomFilter( fpr=0.1)

    items_in_filter = ['hello', 'world', (9, 0, 0), 3, 66.6, -90.2]
    items_not_in_filter = ['goodbye', 'universe', (4, 0, 0), 1, -66.6, 90.2]

    print('Testing Dynamic Bloom Filter')
    for item in items_in_filter:
        BF.add_item(item)

    print('\n Positive items')
    for item in items_in_filter:
        if not BF.query_item(item):
            print('Error! {} should be in the filter, but its not! '.format(item))
        else:
            print('{} is in the filter! '.format(item))

    print('\n Negative items')
    for item in items_not_in_filter:
        if BF.query_item(item):
            print('False positive on item {}! '.format(item))
        else:
            print('{} is not in the filter! '.format(item))
    print()
