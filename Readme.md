# Bloom Filter Scripts Usage

### Requirements
This implementation requires the following packages to be installed:
- `bitarray` - python `bitarray` package, underlying bit information storage
- `mmh3` - murmur hash3 package, the underlying hashing engine for the bloom filter
- `unittest` - python unittest framework for running the tests in `bloomfiltertest.py`

### Using and Running the package
The class definitions and implementation of the bloom filter is included in `bloomfilter.py`.

3 concrete classes of bloom filters have been implemented. These are the `bloomFilterBasic`, `bloomFilter`, and `scalableBloomFilter` class. 

Each of these classes implement the `bloomFilterBase` abstract base class, which has a `add_item(item)` method and an `query_item(item)` method.
The bloomFilter stores information for any item that is immutable (and hashable). This includes strings, ints, floats, 
and tuples. 

If run as main, `bloomfilter.py`
has a few examples showing the use of the three classes. Simply run:
```
python -m bloomfilter
```

To use any of these classes in your own script, simply import it and call the constructor.
For example, a script to use a `bloomFilter` with a capacity of 100 and false positive rate of 0.05 
would look like:
```
from bloomfilter import bloomFilter
BF = bloomFilter(cap=100, fpr=0.05) # constructor
BF.add_item('hello')
needs_to_be_true =  BF.query_item('hello')
```

`bloomfiltertest.py` contains the unittests for the implementations, and can be run:
```
python -m unittest -v bloomfiltertest
```

# Bloom Filter Implementation

The following sections describe the different versions of the `bloomFilters` and the parameters for their constructors.
The UML below describes the class relationship between the 3 bloom filter implementations:

![Bloom Filter UML](/BloomFilter.png) 

The following implementation and analysis assumes the following:
- Hashing function used by the algorithm can hash into every bin with equal probability.
- The computational complexity takes constant time (O(1)) for each call to the i-th hashing function which is implemented as the following:
```
bloomFilter.compute_hash(item, i) = mmh3.hash( str( item__hash__() ), i)
```
- The size of the bitarray in the underlying bloom filter is large (m is large)
- For a bloom filter with a specified capacity, that the number of items inserted does not exceed the initially 
specified capacity

## bloomFilterBasic
`bloomFilterBasic` implements a basic form of the bloom filter, where the number of bits and number of hash functions are
specified by the user. 

**To construct a basic bloom filter with 10 bits and 3 hash functions, do:** 
```
BF = bloomFilterBasic(n_bits=10, n_hash=3)
BF.add_item('hello')
needs_to_be_true =  BF.query_item('hello')
```

There are no limits as to how many items can be inserted into a basic bloom filter, however, the false positive rate 
will go up as a result of inserting a larger number of items into a fixed sized `bloomFilterBasic`

The time complexity for the basic version of the bloom filter for the `add_item` and `query_item` methods is linear 
in the number of hash functions `n_hash` used. Hence it is *O(n_hash)* 

## bloomFilter

Extends `bloomFilterBasic`. This implementation follows the definition and guidelines as outlined in 
https://en.wikipedia.org/wiki/Bloom_filter

`bloomFilter` implements an optimized form of the basic bloom filter by selecting optimized `n_bits` and `n_hash`, to
accomodate a requested capacity `cap` of items to insert, whilst keeping the false positive rate `fpr` within a desired
limit. The formulas for the optimized `n_bits` (denoted *m*) and `n_hash` (denoted *k*), given a `cap` ( *n* ) and
`fpr` ( *p* ) is given:

 *k = round( log_2(p) )*

 *m = - round( (n * ln(p)) / (ln(2) ^ 2) )* 
 
 For large *m*. These values guarantee the expected false positive rate not exceed *p*, as long as the number of items
 inserted does not exceed *n*.

**To construct a `bloomFilter` with a capacity of 10 and a false positive rate of 0.1, do:**
```
BF = bloomFilter(cap=10, fpr=0.1)
BF.add_item('hello')
needs_to_be_true =  BF.query_item('hello')
```

The time complexity of this version of bloom filter, for `add_item` and `query_item` is dependent on the number of hash
functions, which is *O( log(p) )*.

The space complexity is dominated by the size of the underlying bitarray which is *O(n log p)*

## scalableBloomFilter
The scalable consists of one or more `bloomFilter` objects. My implementation follows the design principles as outlined 
in http://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf , with a few modifications made. 
 
Each scalableBloomFilter consists of a list of `bloomFilter` object. It is initialized with a list containing a single 
`bloomFilter` object with an initial capacity `cap0` specified by the user. Items that are added into the 
`scalableBloomFilter` are first added to the initial `bloomFilter` until the estimated number of objects in the filter,
given by the following formula

*n_est = -(m / k) * math.log(1 - (x /m))*

exceeds `cap0`. A second filter is then added to the list of `bloomFilters` with a larger capacity `s*cap0` where `s` is 
a growth rate parameter. When `s` is set to 2, we double the capacity of the next filter every time the previous one fills
up. Every time we add a new item, we query the previous filters first, which prevents the `scalableBloomFilter` from scaling
up unnecessarily.

Setting a false positive ratio for each filter i as `fpr*(r^i)`, where `r` is a positive real less than 1, will guarantee
the overall FPR of the scalable filter to be bounded by `fpr`

To query the `scalableBloomFilter`, we query every `bloomFilter` in the list.

**To construct and use a `scalableBloomFilter` with initial capacity 10 and FPR of 10%, do:** 
```
BF = scalableBloomFilter(cap0=10, fpr=0.1)
BF.add_item('hello')
needs_to_be_true =  BF.query_item('hello')
```

Assuming the number of individual `bloomFilters` in the `scalableBloomFilters` object is given by L, this gives a overall
capacity *n* of:

*n = cap0 * ( 1 + s + s^2 + ... + s^L) = O ( cap0 * s^(L+1) )*  

And the number of filters L is *O( log(n) )*. The bitarray size of each `bloomFilter` *m_i* is given by:

*m_i = cap0 * s^(i-1) log( p * r^i )*

So the total bitarray size of the `scalableBloomFilter` is :

*M = m_1 + m_2 + ... m_L = n_0 (  log( p * r ) + s log( p * r^2 ) + s^(L+1) log( p * r^L ) )*

Which simplifies to become (considering that *L=O(log(cap))*):

*M = O( n * log(p) + n * log(n) )*  

The number of hash functions in the i-th filter is *O(log(p * r^i)) = O(log(p) + i * log(r))*. The maximum 
number of hash functions the query needs to evaluate is therefore given by:

*O(log(p) + i * log(r)) = O(L^2 * log(r) + L * log(p))*

Which gives the final expression for time cost during queries and adding items:

*O( log(n)^2 + log(n) * log(p) )*

# References
1. https://en.wikipedia.org/wiki/Bloom_filter
2. http://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf
 