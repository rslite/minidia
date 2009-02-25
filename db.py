
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
		self.pres = ''
		self.dd = []
		self.ww = []
	def __repr__(self):
		return '%s\nDDD:\n%s\nWWW:\n%s' % (self.pres, repr(self.dd), repr(self.ww))

class DB:
	def __init__(self):
		self.db = []
		self._read_db()
	def __repr__(self):
		return repr(self.db)

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
						self.db.append(section)
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
					if len(minidiag.pres):
						minidiag.pres += '\n'
					minidiag.pres += l
				elif state == D:
					minidiag.dd.append(l)
				elif state == W:
					minidiag.ww.append(l)
		f.close()

def main():
	db = DB()
	print db

if __name__ == '__main__':
	main()
