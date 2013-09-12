import multiprocessing as mp
import numpy as np


def arr_add_field(arr, new_field, vals):
    """
    Adds a new field to a structured array.
    This is a handy function for adding new metadata to 
    the original metadata array in Corpus object.
    
    **Parameters**

    arr : array
        A structured array.
    new_field : string
        The dtype name for the values.
    vals : list
        A list of values. `vals` must have the same length as `arr`.

    **Returns**

    New array with the added values.

    **See Also**
    
    Corpus.view_metadata

    **Examples**

    >>> arr = np.array([('a', 1), ('b', 2), ('c', 3)], 
            dtype=[('field', '|S4'), ('i', '<i4')])
    >>> vals = [-1, -2, -3]
    >>> arr_add_field(arr, 'neg_i', vals)
    array([('a', 1, -1), ('b', 2, -2), ('c', 3, -3)], 
          dtype=[('field', '|S4'), ('i', '<i4'), ('neg_i', '<i8')])
    """
    # Constructing new dtype
    new_dtype = np.array(vals).dtype
    dt = [(n, arr.dtype[n]) for n in arr.dtype.names]
    dt.append((new_field, new_dtype))

    # Building new structured array
    new_arr = np.empty_like(arr, dtype=dt)
    for n in new_arr.dtype.names:
        if n == new_field:
            new_arr[n][:] = vals[:]
        else:
            new_arr[n][:] = arr[n][:]

    return new_arr
    

def enum_matrix(arr, axis=0, indices=[], field_name='i'):
    """
    Takes a 1-dimensional or 2-dimensional array and returns a sorted
    structured array with indices.

    **Parameters**

    arr : array
        1-dimensional or 2-dimensional numpy array.
    axis : int, optional
        Array axis 0 or 1. Default is 0.
    indices : list, optional
        List of indices. If 'indices' is empty, then `indices` is set to
        a range of indices for the length of `arr`. Default is an empty list.
    field_name : string, optional
        Name for indices in the structured array dtype. Default is 'i'.

    **Returns**

    A sorted structured array with indices.

    **See Also**

    zip_arr

    **Examples**

    >>> arr = np.array([[6,3,7],[2,0,4]])
    >>> enum_matrix(arr)
    array([[(2, 7), (0, 6), (1, 3)],
           [(2, 4), (0, 2), (1, 0)]], 
           dtype=[('i', '<i8'), ('value', '<i8')])
    """
    #if len(indices) == 0:
    #    indices = np.arange(arr.shape[1])
    if len(indices) == 0 and len(arr.shape) > 1:
        indices = np.arange(arr.shape[1])

    ind = np.array([indices.copy() for i in xrange(arr.shape[0])])
    dt = [(field_name, indices.dtype), ('value', arr.dtype)]
    mt = zip_arr(ind, arr, field_names=[field_name, 'value'])

    if len(arr.shape) > 1:
        if axis:
            for i in xrange(arr.shape[axis]):
                idx = np.argsort(mt['value'][:,i])
                mt[field_name][:,i] = ind[:,i][idx]
                mt['value'][:,i] = arr[:,i][idx]
                mt[:,i] = mt[:,i][::-1]	
        else:
            for i in xrange(arr.shape[axis]):
                idx = np.argsort(mt['value'][i])
                mt[field_name][i] = ind[i][idx]
                mt['value'][i] = arr[i][idx]
                mt[i,:] = mt[i,:][::-1]
    else:
        idx = np.argsort(arr)
        mt[field_name][:] = idx[:]
        mt['value'][:] = arr[idx]

    return mt


    
def enum_sort(arr, indices=[], field_name='i', filter_nan=False):
    """
    Takes a 1-dimensional array and returns a sorted array with matching
    indices from the original array.

    **Parameters**

    arr : array
        A structured 1-dimensional array.
    indices : list, optional
        List of indices. If `indices` is empty, then `indices` is set to
        a range of indices for the length of `arr`. Default is an empty list.
    field_name : string, optional
        Name for indices in the structured array dtype. Default is 'i'.
    filter_nan : boolean, optional
        If True, Not a Number values are filtered. Default is False.

    **Returns**
    
    A sorted structured array.

    **Examples**

    >>> arr = np.array([7,3,1,8,2])
    >>> enum_sort(arr)
    array([(3, 8), (0, 7), (1, 3), (4, 2), (2, 1)], 
          dtype=[('i', '<i8'), ('value', '<i8')])
    """
    idx = np.argsort(arr)
    if len(indices) == 0:
        indices = np.arange(arr.shape[0])
    else:
        indices = np.array(indices)
	
    dt = [(field_name, indices.dtype), ('value', arr.dtype)]

    new_arr = np.empty(shape=arr.shape, dtype=dt)
    new_arr[field_name] = indices[idx]
    new_arr['value'] = arr[idx]

    if filter_nan:
        new_arr = new_arr[np.isfinite(new_arr['value'])]
        
    return new_arr[::-1]

 

def enum_array(arr, indices=[], field_name='i'):
    """
    Takes an array and returns a structured array with indices
    and values as dtype names.

    **Parameters**
    
    arr : array
        1-dimensional array
    indices : list, optional
        List of indices. If `indices` is empty, then `indices` is set to
        a range of indices for the length of `arr`. Default is an empty list.
    field_name : string, optional 
        Name for indices in the structured array dtype. Default is 'i'.

    **Returns**

    A structured array with indices and value fields.

    **See Also**

    zip_arr

    **Examples**

    >>> arr = np.array([7,3,1,8,2])
    >>> enum_array(arr)
    array([(0, 7), (1, 3), (2, 1), (3, 8), (4, 2)], 
          dtype=[('i', '<i8'), ('value', '<i8')])
    """
    if len(indices) == 0:
        indices = np.arange(arr.size)
    else:
        indices = np.array(indices)
    return zip_arr(indices, arr, field_names=[field_name, 'value'])



def zip_arr(arr_1, arr_2, field_names=['arr_1','arr_2']):
    """
    Takes two arrays with same shape and returns a zipped structured array.

    **Parameters**

    arr_1 : array
        1-dimensional array.        
    arr_2 : array
        1-dimensional array.
    field_names : list, optional
        List of numpy dtype names.

    **Returns**

    Zipped array of `arr_1` and `arr_2`.

    **Examples**

    >>> a1 = np.array([[2,4], [6,8]])
    >>> a2 = np.array([[1,3],[5,7]])
    >>> zip_arr(a1, a2, field_names=['even', 'odd'])
    array([[(2, 1), (4, 3)],
           [(6, 5), (8, 7)]], 
           dtype=[('even', '<i8'), ('odd', '<i8')])
    """
    if field_names:
        dt = [(field_names[0], arr_1.dtype), (field_names[1], arr_2.dtype)]

    new_arr = np.empty_like(arr_1, dtype=dt)

    new_arr[new_arr.dtype.names[0]][:] = arr_1[:]
    new_arr[new_arr.dtype.names[1]][:] = arr_2[:]
    
    return new_arr


def map_strarr(arr, m, k, new_k=None):
    """
    Takes a structured array `arr`, a field name `k` and an Indexable
    `m` and returns a copy of `arr` with its field `k` values mapped
    according to `m`. If `new_name` is given, the field name `k` is
    replaced with `new_name`.

    **Parameters**

    arr : array

    m : iterable
        An indexable array or list to retrieve the values from.
        The iterable contains values to replace the original `k` values.
    k : string
        Field name with values to be replaced. arr[k] should be an integer
        type.
    new_k : string, optional
        Field name for the new values. Default is None, which is then set to
        `k`, the original field name.

    **Returns**
    
    A new array with `k` values replaced by values in `m`.

    **Examples**

    >>> arr = np.array([(0, 1.), (1, 2.)], dtype=[('i', 'i4'), ('v', 'f4')])
    >>> m = ['foo', 'bar']
    >>> map_strarr(arr, m, 'i', 'string')
    array([('foo', 1.0), ('bar', 2.0)], 
          dtype=[('string', '|S3'), ('v', '<f4')])
    """
    # Constructing new dtype
    if not new_k:
        new_k = k
    k_vals = np.array([m[i] for i in arr[k]])
    dt = [(n, arr.dtype[n]) for n in arr.dtype.names]
    i = arr.dtype.names.index(k)
    dt[i] = (new_k, k_vals.dtype)

    # Building new structured array
    new_arr = np.empty_like(arr, dtype=dt)
    for n in new_arr.dtype.names:
        if n == new_k:
            new_arr[new_k][:] = k_vals[:]
        else:
            new_arr[n][:] = arr[n][:]

    return new_arr


def mp_split_ls(ls, n):
    """
    Split list into an `n`-length list of arrays.

    **Parameters**

    ls : list

    n : int

    **Returns**
    
    List of arrays whose length is 'n'.

    **Examples**
    >>> ls = [1,5,6,8,2,8]
    >>> mp_split_ls(ls, 4)
    [array([1, 5]), array([6, 8]), array([2]), array([8])]
    """
    return np.array_split(ls, min(len(ls), n))


def mp_shared_array(arr, ctype='i'):
    
    shared_arr_base = mp.Array(ctype, arr.size)
    shared_arr_base[:] = arr
    return np.ctypeslib.as_array(shared_arr_base.get_obj())


def mp_shared_value(x, ctype='i'):

    return mp.Value(ctype, x)


def isstr(x):
    """
    Returns True if `x` is an instance of a string.
    """
    return isinstance(x, basestring) or isinstance(x, np.flexible)


def isint(x):
    """
    Returns True if `x` is an instance of an int.
    """
    return (isinstance(x, np.integer) 
            or isinstance(x, int) or isinstance(x, long))


def isfloat(x):
    """
    Returns True if `x` is an instance of a float.
    """
    return (isinstance(x, np.inexact) or isinstance(x, np.float))


#
# Testing
#


def arr_add_field_test():

    arr = np.array([(1, '1'), (2, '2'), (3, '3')],
                   dtype=[('i', np.int), ('c', '|S1')])
    new_arr = np.array([(1, '1', 0), (2, '2', 0), (3, '3', 0)],
                       dtype=[('i', np.int), ('c', '|S1'), ('new', np.int)])

    new_field = 'new'
    vals = np.zeros(3, dtype=np.int)

    test_arr = arr_add_field(arr, new_field, vals)

    assert (new_arr==test_arr).all()
    assert new_arr.dtype==test_arr.dtype



def test_map_strarr():

    arr = np.array([(0, 1.), (1, 2.)], 
                   dtype=[('i', 'i4'), ('v', 'f4')])
    m = ['foo', 'bar']
    arr = map_strarr(arr, m, 'i', new_k='str')

    assert (arr['str'] == np.array(m, dtype=np.array(m).dtype)).all()
    assert (arr['v'] == np.array([1., 2.], dtype='f4')).all()


def mp_split_ls_test():

    l = [slice(0,0), slice(0,0), slice(0,0)]
    assert len(mp_split_ls(l, 1)) == 1
    assert (mp_split_ls(l, 1)[0] == l).all()
    assert len(mp_split_ls(l, 2)) == 2
    assert (mp_split_ls(l, 2)[0] == [slice(0,0), slice(0,0)]).all()
    assert (mp_split_ls(l, 2)[1] == [slice(0,0)]).all()
    assert len(mp_split_ls(l, 3)) == 3
    assert (mp_split_ls(l, 3)[0] == [slice(0,0)]).all()
    assert (mp_split_ls(l, 3)[1] == [slice(0,0)]).all()
    assert (mp_split_ls(l, 3)[2] == [slice(0,0)]).all()
