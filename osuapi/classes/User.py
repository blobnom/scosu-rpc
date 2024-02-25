class SearchedUser:
	id: int
	name: str

	def __init__(self, data: dict):
		self.id = data["id"]
		self.name = data["name"]
	
	def __str__(self) -> str:
		return str(vars(self))
	
class UserInfo(SearchedUser):
	country: str
	user_created: int
	last_seen: int

	def __init__(self, data: dict):
		self.id = data["id"]
		self.name = data["name"]
		self.country = str(data["country"]).upper()
		self.user_created = data["creation_time"]
		self.last_seen = data["latest_activity"]
		
	def __str__(self) -> str:
		return str(vars(self))
	
class UserGrades:
	xh: int
	x: int
	sh: int
	s: int
	a: int

	def __init__(self, data: dict):
		self.xh = data["xh_count"]
		self.x = data["x_count"]
		self.sh = data["sh_count"]
		self.s = data["s_count"]
		self.a = data["a_count"]
	
	def __str__(self) -> str:
		return str(vars(self))
	
class UserStats:
	mode: int
	global_rank: int
	country_rank: int
	total_score: int
	ranked_score: int
	playcount: int
	playtime: int
	accuracy: float
	grades: UserGrades

	def __init__(self, data: dict):
		self.mode = data["mode"]
		self.global_rank = data["rank"]
		self.country_rank = data["country_rank"]
		self.total_score = data["tscore"]
		self.ranked_score = data["rscore"]
		self.playcount = data["plays"]
		self.playtime = data["playtime"]
		self.accuracy = data["acc"]
		self.grades = UserGrades(data)
	
	def __str__(self) -> str:
		return str(vars(self))

class UserFull:
	info: UserInfo
	stats: UserStats

	def __init__(self, data: dict):
		self.info = UserInfo(data["info"])
		self.stats = UserStats(data["stats"])
		
	def __str__(self) -> str:
		return str(vars(self))