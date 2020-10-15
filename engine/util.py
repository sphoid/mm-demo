def hex_to_rgb(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# def partial_dict_key(key, d):
# 	for k, v in d.iteritems():
# 		if all(k1 == k2 or k2 is None  for k1, k2 in zip(k, key)):
# 			yield v

