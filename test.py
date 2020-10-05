def partial(key, d):
	for k, v in d.iteritems():
		if all(k1 == k2 or k2 is None  for k1, k2 in zip(k, key)):
			yield v

d = {(1, 1): 'tile 1x1', (1, 2): 'tile 1x2', (1, 3): 'tile 1x3', (2, 1): 'tile 2x1', (2, 2): 'tile 2x2', (2, 3): 'tile 2x3'}

print(list(partial((2, None), d)))