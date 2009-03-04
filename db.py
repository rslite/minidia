#!/usr/bin/python

from optparse import OptionParser
import ctypes, difflib, random, re, sys

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12
try:
	stdout = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
except:
	stdout = None

# Colors for good, bad and good but badly ordered responses
COL_OK, COL_BAD, COL_SEMIOK = 10, 12, 14
# Match threshold to consider a good response
GOOD_THRESHOLD = 0.8

def setcol(col):
	if stdout:
		return ctypes.windll.kernel32.SetConsoleTextAttribute(stdout, col)
	else:
		return False

def hilite(txt, col=15, nl=True):
	""" Highlight a text with the provided color then go back to the normal one """
	global opts
	if opts.nocolor:
		print txt,
		if nl: print
		return
	# Set color, print text and go back to default color
	setcol(col)
	print txt,
	if nl: print
	setcol(7)

class Section:
	def __init__(self, name):
		self.name = name
		self.kh = self.kpe = ''
		self.diags = []
	def __getitem__(self, n):
		return self.diags[n]
	def __len__(self):
		return len(self.diags)
	def __repr__(self):
		return 'SEC: %s\nKH: %s\nKPE: %s\n%s' % (self.name, self.kh, self.kpe, repr(self.diags))

class MiniDiag:
	crt = 0
	def __init__(self):
		MiniDiag.crt += 1
		self.id = MiniDiag.crt
		self.presentation = ''
		self.dd = []
		self.ww = []
	def __repr__(self):
		return '%d. %s\nDDD:\n%s\nWWW:\n%s' % (self.id, self.presentation, repr(self.dd), repr(self.ww))
	def __str__(self):
		str = '%d. %s\n\n' % (self.id, self.presentation)
		for i,v in enumerate(self.dd):
			str += '  D %d: %s\n' % (i+1, v)
		str += '\n'
		for i,v in enumerate(self.ww):
			str += '  W %d: %s\n' % (i+1, v)
		return str

class DB:
	def __init__(self):
		self.sections = []
		self._read_db()
	def __repr__(self):
		return repr(self.sections)

	def random_all(self):
		""" Get a random test from all available """
		sec = random.choice(self.sections)
		t = random.choice(sec.diags)
		return t

	def get_test(self, id):
		""" Get a test based on its id """
		for s in self.sections:
			if s.diags[0].id <= id <= s.diags[-1].id:
				diag = filter(lambda d: d.id == id, s.diags)
				if diag:
					return diag[0]
				break
		#No diag found so throw an exception
		raise Exception("Diag with id '%d' not found" % id)

	def _read_db(self):
		f = open('db.txt')
		SEC, KH, KPE, P, D, W = range(6)
		state = SEC
		states = {'S':SEC, 'Key History':KH, 'Key Physical Exam':KPE, 'P':P, 'D':D, 'W':W}
		minidiag = section = None
		for l in f:
			l = l.strip()
			if not l or l[0]=='#': continue
			if l[0] == ':':
				#Command - change state
				state = states[l[1:]]
				if state == P:
					if minidiag:
						section.diags.append(minidiag)
					minidiag = MiniDiag()
			else:
				#Add data to current state
				if state == SEC:
					if section:
						self.sections.append(section)
					section = Section(l)
					minidiag = None
				elif state == KH:
					if len(section.kh):
						section.kh += '\n'
					section.kh += l
				elif state == KPE:
					if len(section.kpe):
						section.kpe += '\n'
					section.kpe += l
				elif state == P:
					if len(minidiag.presentation):
						minidiag.presentation += '\n'
					minidiag.presentation += l
				elif state == D:
					minidiag.dd.append(l)
				elif state == W:
					minidiag.ww.append(l)
		f.close()

class Test:
	#Cleaner expression to remove parenthesis
	rg_cleaner = re.compile('\s*\(.*?\)\s*')

	def __init__(self, md):
		self.minidiag = md
		self.dd = []
		self.ww = []

	def administer(self):
		print '%d. %s' % (self.minidiag.id, self.minidiag.presentation)
		print '-----'
		for i in xrange(20):
			res = raw_input('D %d: ' % (i+1))
			if not res:
				break
			self.dd.append(res)
		print '-----'
		for i in xrange(20):
			res = raw_input('W %d: ' % (i+1))
			if not res:
				break
			self.ww.append(res)

	def show(self, with_md=True):
		"""
		Show the results of a test.
		with_md - if True show initial minidiag 
		Returns the calculated points for this md
		"""

		def show_resp(title, known, answered):
			"""
			Show a set of results for D or W 
			Returns the calculated points for this set
			The points are calculated like this:
			0.00 - bad
			0.75 - good, but in bad position
			1.00 - all good
			"""
			hilite(title, 9)

			total = 0.0
			for i,v in enumerate(answered):
				col, points = COL_BAD, 0.0
				sm = difflib.SequenceMatcher(None, v.lower(), '')
				ratios = []
				max_ratio = 0
				for j,d in enumerate(known):
					sm.set_seq2(Test.rg_cleaner.sub('', d.lower()))
					r = sm.ratio()
					ratios.append('%.2f' % r)
					if r >= GOOD_THRESHOLD and r > max_ratio:
						max_ratio = r
						col, points = (COL_OK, 1.0) if i==j else (COL_SEMIOK, 0.75)
				print ' ', (i+1),
				chr = '-..+*'[int(points*4)]
				hilite(chr, 11, nl=False)
				hilite(v, col)
				if opts.verbose:
					print '    ', ' '.join(ratios)
				# Update the total points
				total += points/len(known)
			print 'Total: %.2f' % total
			return total


		print '=================='
		if with_md:
			print self.minidiag
		
		p1 = show_resp("Resp D", self.minidiag.dd, self.dd)
		p2 = show_resp("Resp W", self.minidiag.ww, self.ww)
		#Calculate points as mean between the two sets of answers
		p = (p1+p2)/2
		if p < 0.5: col = 12 #red
		elif p < 0.8: col = 14 #yellow
		else: col=10 #green
		hilite('-- %.2f -- %s' % (p, '*' * int(p*20)), col)
		return p

class Tester:
	def __init__(self, db):
		self.db = db

	def init_session(self):
		""" Init a testing session """
		# Clear the screen (no peeking :))
		print '\n' * 30
		hilite('*** New session ***')
		self.tests = []
		self.seen_ids = []

	def random_test(self):
		""" Administer a random test """
		while True:
			md = self.db.random_all()
			if not md.id in self.seen_ids:
				break
		self.seen_ids.append(md.id)
		self._administer(md)
	
	def id_test(self, id):
		""" Administer a test based on id """
		md = self.db.get_test(id)
		self._administer(md)

	def _administer(self, md):
		tr = Test(md)
		tr.administer()
		self.tests.append(tr)

	def results(self):
		""" Print the results of the test """
		hilite('*** Test results ***')
		for i,t in enumerate(self.tests):
			hilite('* Result %d of %d *' % (i+1, len(self.tests)))
			t.show()

def main():
	parser = OptionParser()
	parser.add_option("-r", "--randomize", dest="rand_seed", type="int", help="seed for randomizer")
	parser.add_option("-c", "--crt", dest="id", type="int", help="show a specific question based on its current number")
	parser.add_option("-n", "--number", dest="number", type="int", default=1, help="number of tests to administer (default 1)")
	parser.add_option("-i", "--info", dest="show_info", action='store_true', default=False, help="show DB info and exit")
	parser.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False, help="increase output verbosity")
	parser.add_option("", "--nocolor", dest="nocolor", action='store_true', default=False, help="don't use console coloring")
	global opts
	(opts, args) = parser.parse_args()
	if opts.rand_seed:
		random.seed(int(opts.rand_seed))
	
	db = DB()

	# If needed show DB info and exit
	if opts.show_info:
		for s in db.sections:
			hilite('%3d - %3d: %s' % (s.diags[0].id, s.diags[-1].id, s.name))
			if opts.verbose:
				print s.kh
				hilite('-------')
				print s.kpe
				hilite('-------')
		return

	tester = Tester(db)
	tester.init_session()
	if opts.id:
		tester.id_test(opts.id)
	else:
		for n in xrange(opts.number):
			hilite('* Test %d of %d *' % (n+1, opts.number))
			tester.random_test()
	tester.results()

if __name__ == '__main__':
	main()
