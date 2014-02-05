def n2sh(num):

	if num >= 1e+06:		
		num = num/1e+06
		dec = "{:2.1f}".format(num)
		sh = dec + "M"

	elif num >= 1e+03:
		num = num/1e+03
		dec = "{:2.1f}".format(num)
		sh = dec + "K"

	else:
		sh = str(num)

	return sh