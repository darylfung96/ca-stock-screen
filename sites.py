from abc import ABC
import time
import numpy as np
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


class Screener(ABC):

	def __init__(self):
		...

	@property
	def driver(self):
		raise NotImplementedError

	def start_process(self):
		raise NotImplementedError


class TradingViewScreener(Screener):

	def __init__(self):
		super(TradingViewScreener, self).__init__()
		chrome_options = uc.ChromeOptions()
		chrome_options.add_argument("--disable-popup-blocking")
		chrome_options.add_argument("--incognito")
		self._driver = uc.Chrome(driver_executable_path='/Applications/chromedriver',
		                         options=chrome_options, proxy_options=None)
		self._driver.maximize_window()
		self.wait_driver = WebDriverWait(self.driver, 400)

	@property
	def driver(self):
		return self._driver

	def give_scores(self, item_list, is_descending=False):
		indexes = np.array(item_list).argsort()
		scores = [0] * len(item_list)

		for i in range(len(indexes)):
			if is_descending:
				scores[indexes[i]] = len(item_list) - i
			else:
				scores[indexes[i]] = i + 1

		return scores

	def start_process(self):
		self.driver.get('https://www.tradingview.com/markets/stocks-canada/sectorandindustry-sector/')

		self.wait_driver.until(EC.presence_of_element_located((By.XPATH, "//div[@data-field='market_cap_basic']")))
		# click twice to sort from largest to smallest
		market_cap_header = self.driver.find_elements(By.XPATH, "//div[@data-field='market_cap_basic']")[0]
		time.sleep(1)
		market_cap_header.click()
		time.sleep(1)
		market_cap_header.click()
		time.sleep(1)

		sectors = self.driver.find_elements(By.XPATH, "//a[@rel='noopener']")
		sectors_text = [sector.text for sector in sectors]
		sectors = [sector.get_attribute('href') for sector in sectors]

		count = 5
		for sector_index, sector in enumerate(sectors):
			companies = []
			technical_ratings = []
			eps = []
			margins = []
			current_ratios = []
			debt_to_equities = []

			technical_rating_scores, eps_scores, margin_scores, current_ratio_scores, debt_to_equity_scores = [], [], [], [], []

			print(sectors_text[sector_index])
			print('========================================================================')
			self.driver.get(sector)

			market_cap_header = self.driver.find_elements(By.XPATH, "//th[@data-field='market_cap_basic']")[0]
			time.sleep(1)
			market_cap_header.click()
			time.sleep(1)
			market_cap_header.click()
			time.sleep(1)

			selected_companies = self.driver.find_elements(By.CLASS_NAME, 'tv-screener__symbol')[:count]
			for selected_company in selected_companies:
				companies.append(selected_company.text)

			technical_ratings = self.get_top_overviews(count)
			eps = self.get_top_eps(count)
			time.sleep(1)
			margins = self.get_top_margins(count)
			time.sleep(1)
			current_ratios, debt_to_equities = self.get_top_balance_sheet(count)

			technical_rating_scores = np.array(self.give_scores(technical_ratings))
			eps_scores = np.array(self.give_scores(eps))
			margin_scores = np.array(self.give_scores(margins))
			current_ratio_scores = np.array(self.give_scores(current_ratios))
			debt_to_equity_scores = np.array(self.give_scores(debt_to_equities, is_descending=True))

			total_scores = technical_rating_scores + eps_scores + margin_scores + current_ratio_scores + debt_to_equity_scores

			indexes = total_scores.argsort()
			for i in range(len(companies)):
				print(companies[indexes[i]], ' ', total_scores[indexes[i]])

			print()
			print()

	def switch_tab(self, tab_name):
		self.driver.find_elements(By.CLASS_NAME, 'itemsWrap-1EEezFCx')[0].find_elements(By.XPATH,
		                                                                                f"//*[text()='{tab_name}']")[
			-1].click()
		time.sleep(1)

	def get_top_overviews(self, count):
		tech_rating_dict = {'strong sell': -2, 'sell': -1, 'neutral': 0, 'buy': 1, 'strong buy': 2}
		technical_ratings = self.driver.find_elements(By.CLASS_NAME, 'tv-screener-table__signal')[:count]

		technical_ratings_list = []
		for technical_rating in technical_ratings:
			score = tech_rating_dict[technical_rating.text.lower()]
			technical_ratings_list.append(score)
		return technical_ratings_list

	def get_top_eps(self, count):
		eps = self.driver.find_elements(By.XPATH, '//td[@data-field-key="earnings_per_share_basic_ttm"]')[:count]
		eps = [float(re.sub(r'[^\x00-\x7F]+','-', current_eps.text.replace('CAD', ''))) if len(current_eps.text) > 1 else 0 for current_eps in eps]
		return eps

	def get_top_margins(self, count):
		self.switch_tab('Margins')
		margins = self.driver.find_elements(By.XPATH, "//td[@data-field-key='after_tax_margin']")[:count]
		margins = [float(re.sub(r'[^\x00-\x7F]+', '-', margin.text.replace('%', ''))) if len(margin.text) > 1 else 0 for margin in margins]
		return margins

	def get_top_balance_sheet(self, count):
		self.switch_tab('Balance Sheet')
		current_ratios = self.driver.find_elements(By.XPATH, "//td[@data-field-key='current_ratio']")[:count]
		current_ratios = [float(current_ratio.text) if len(current_ratio.text) > 1 else 0 for current_ratio in current_ratios] # sometimes no quick ratio, so it just shows '-' we will use the length to check

		debt_to_equities = self.driver.find_elements(By.XPATH, "//td[@data-field-key='debt_to_equity']")[:count]
		debt_to_equities = [float(re.sub(r'[^\x00-\x7F]+', '-', debt_to_equity.text)) for debt_to_equity in debt_to_equities]

		return current_ratios, debt_to_equities

