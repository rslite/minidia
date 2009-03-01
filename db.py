#!/usr/bin/python

from optparse import OptionParser
import ctypes, difflib, random, sys

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

		def show_resp(title, known, answered):
			setcol(9)
			print title
			setcol(7)

			for i,v in enumerate(answered):
				col = COL_BAD
				sm = difflib.SequenceMatcher(None, v.lower(), '')
				ratios = []
				for j,d in enumerate(known):
					sm.set_seq2(d.lower())
					r = sm.ratio()
					ratios.append('%.2f' % r)
					if r >= GOOD_THRESHOLD:
						col = COL_OK if i==j else COL_SEMIOK
				print ' ', (i+1),
				setcol(col)
				print v,
				setcol(7)
				print '    ', ' '.join(ratios)


		print '=================='
		if with_md:
			print self.minidiag
		
		show_resp("Resp D", self.minidiag.dd, self.dd)
		show_resp("Resp W", self.minidiag.ww, self.ww)

		print '------------------'

class Tester:
	def __init__(self, db):
		self.db = db

	def init_session(self):
		""" Init a testing session """
		print "*** New session ***"
		self.tests = []

	def random_test(self):
		""" Administer a random test """
		md = self.db.random_all()
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
		print "*** Test results ***"
		for t in self.tests:
			t.show()

def main():
	parser = OptionParser()
	parser.add_option("-r", "--randomize", dest="rand_seed", type="int", help="seed for randomizer")
	parser.add_option("-i", "--id", dest="id", type="int", help="show a specific question based on its id")
	(opts, args) = parser.parse_args()
	if opts.rand_seed:
		random.seed(int(opts.rand_seed))
	db = DB()
	tester = Tester(db)
	tester.init_session()
	if opts.id:
		tester.id_test(opts.id)
	else:
		tester.random_test()
	tester.results()

if __name__ == '__main__':
	main()
