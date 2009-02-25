import random

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
	def __init__(self):
		self.presentation = ''
		self.dd = []
		self.ww = []
	def __repr__(self):
		return '%s\nDDD:\n%s\nWWW:\n%s' % (self.presentation, repr(self.dd), repr(self.ww))

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
		print self.minidiag.presentation
		for i in xrange(5):
			res = raw_input('D %d:' % i)
			self.dd.append(res)
		for i in xrange(5):
			res = raw_input('W %d:' % i)
			self.ww.append(res)

	def show(self, with_md=True):
		print '------------------'
		if with_md:
			print repr(self.minidiag)
		print "RESP_D"
		print '\n'.join(self.dd)
		print "RESP_W"
		print '\n'.join(self.ww)
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
		tr = TestResponse(md)
		tr.administer()


	def results(self):
		""" Print the results of the test """
		print "*** Test results ***"

def main():
	db = DB()
	tester = Tester(db)
	tester.init_session()
	tester.random_test()
	tester.results()

if __name__ == '__main__':
	main()
