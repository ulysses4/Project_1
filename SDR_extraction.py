#!/usr/bin/python

import pandas as pd
from datetime import date, datetime, timedelta
import time
import math

#needed for sending emails
import csv
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
import smtplib

from func_email import csv2htmlTableStr as csv2html

from dateutil import relativedelta

def format_col(df):
	"""formats column names and creates some new ones"""
	df.rename(columns={"EXECUTION_TIMESTAMP":"EXECUTION_TIME",
						"CLEARED":"C/U",
						"EXECUTION_VENUE":"SEF",
						"EFFECTIVE_DATE":"START",
						"END_DATE":"END",
						"SETTLEMENT_CURRENCY":"CUR",
						"PRICE_FORMING_CONTINUATION_DATA":"TYPE",
						"UNDERLYING_ASSET_1":"LEG1",
						"UNDERLYING_ASSET_2":"LEG2",
						"PRICE_NOTATION":"LEVEL",
						"ADDITIONAL_PRICE_NOTATION":"FEE",
						"ROUNDED_NOTIONAL_AMOUNT_1":"SIZE"},
						inplace=True)

	df["DATE"] = df["EXECUTION_TIME"].apply(lambda x: x.date().
											strftime("%m/%d/%y"))

	df["TIME"] = df["EXECUTION_TIME"].apply(lambda x: x.time())

	df["DATE"] = pd.to_datetime(df["DATE"])
	df["START"] = pd.to_datetime(df["START"])
	df["END"] = pd.to_datetime(df["END"])

	df["TERM"] = map(lambda td: datetime(1,1,1) + td, list(df["END"]-df["DATE"]))
	df["TERM"] = df["TERM"].apply(lambda x: "{0}y{1}m".format(x.year-1, x.month-1))
	df["TERM"] = df["TERM"].apply(lambda x: x.replace("0m",""))

	df["AGED"] = map(lambda td: "" if td else "aged", list(df["START"]>df["DATE"]))

	#df["TERM"] = (df["END"] - df["START"]).dt.days/365

	df["DATE"] = df["DATE"].apply(lambda x: x.strftime("%m/%d/%y"))
	df["START"] = df["START"].apply(lambda x: x.strftime("%m/%d/%y"))
	df["END"] = df["END"].apply(lambda x: x.strftime("%m/%d/%y"))

	df["SIZE"] = df["SIZE"].apply(lambda x: int(float(x.replace(",",""))/1000000.0))

	df["FEE"] = df["FEE"].apply(lambda x: "-" if isinstance(x,float) else\
				str(int(float(x.replace(",",""))/1000.0))+"k")

	dict_type = dict({"Trade":"TR", "Novation":"NV", "Amendment":"AM",
						"Termination":"TE"})

	df["TYPE"] = df["TYPE"].apply(lambda x: dict_type[x])

	include_columns = ["DATE",
						"TIME",
						"TYPE",
						"SIZE",
						"AGED",
						"TERM",
						"LEVEL",
						"FEE",
						"START",
						"END",
						"C/U",
						"SEF"]

	df = df[include_columns]

	return df

def filter_SDR(df):
	"""divides a single df into multiple df's by record type"""
	try:
		df = df[df.ACTION == "NEW"] #takes out CANCEL or CORRECT actions
		df = df[df.SETTLEMENT_CURRENCY == "USD"]
		df = df[df.TAXONOMY == "InterestRate:IRSwap:Inflation"]
		df.reset_index(drop=True, inplace=True)

		df.EXECUTION_TIMESTAMP = df.EXECUTION_TIMESTAMP.apply(\
		lambda x: datetime.strptime(x.replace("T", " "), "%Y-%m-%d %H:%M:%S"))

		#returns all client ASW's (trade, termiantion, novation)
		df_asw = df[((df.EXECUTION_VENUE == "OFF") &\
					((df.UNDERLYING_ASSET_1 == "USD-LIBOR-BBA") |\
					 (df.UNDERLYING_ASSET_2 == "USD-LIBOR-BBA")))]

		df_trade = df[(df.EXECUTION_VENUE == "OFF") &\
				   (df.PRICE_FORMING_CONTINUATION_DATA == "Trade") &\
				   (df.UNDERLYING_ASSET_1 != "USD-LIBOR-BBA") &\
				   (df.UNDERLYING_ASSET_2 != "USD-LIBOR-BBA")]

		df_termination = df[(df.EXECUTION_VENUE == "OFF") &\
						(df.PRICE_FORMING_CONTINUATION_DATA == "Termination") &\
						(df.UNDERLYING_ASSET_1 != "USD-LIBOR-BBA") &\
						(df.UNDERLYING_ASSET_2 != "USD-LIBOR-BBA")]


		df_novation = df[(df.EXECUTION_VENUE == "OFF") &\
						 (df.PRICE_FORMING_CONTINUATION_DATA == "Novation") &\
						 (df.UNDERLYING_ASSET_1 != "USD-LIBOR-BBA") &\
						 (df.UNDERLYING_ASSET_2 != "USD-LIBOR-BBA")]

		#returns all broker trades (ZC and ASW)
		df_broker = df[(df.EXECUTION_VENUE == "ON") &\
					(df.PRICE_FORMING_CONTINUATION_DATA == "Trade")]

		df_asw = format_col(df_asw)
		df_trade = format_col(df_trade)
		df_termination = format_col(df_termination)
		df_novation = format_col(df_novation)
		df_broker = format_col(df_broker)

		return df_asw, df_trade, df_termination, df_novation, df_broker

	except:
		print "Error has occurred"
		a = pd.DataFrame()
		return a, a, a, a, a

def send_email(table_file_list, run_dt):
	"""takes the list of files and send them out as tables in email"""

	#login details
	me = "igor.cashyn@gmail.com"
	pw = "Maxima90"
	server = "smtp.gmail.com:587"
	you = "igor.cashyn@gmail.com"

	table_list = []

	for table_file in table_file_list:
		table_list.append(csv2html("/Users/icashyn/JPM/DTCC/"+table_file))

	text = "\n"
	html = "<html><body>\n"

	for i in range(0, len(table_list)):
		text += table_file_list[i].replace(".csv","").upper() +\
				"\n" + table_list[i] + "\n"

		html += """<p><font size="2", color="red">""" +\
				table_file_list[i].replace(".csv","").upper() +\
				"</font></p>\n" + table_list[i] + "<br>"

	html += "</body></html>"

	message = MIMEMultipart("alternative", None, [MIMEText(text),
				MIMEText(html, "html")])

	message["Subject"] = "SDR Trades* (" + run_dt.strftime("%m-%d-%y") + ")"
	message["From"] = me
	message["To"] = you
	server = smtplib.SMTP(server)
	server.ehlo()
	server.starttls()
	server.login(me, pw)
	server.sendmail(me, you, message.as_string())
	server.quit()

	return 0

def run_RT(run_dt):
	"""runs real time"""
	url_base = "https://kgc0418-tdw-data2-0.s3.amazonaws.com/slices/SLICE_RATES_"

	df_sum_asw = pd.DataFrame()
	df_sum_trade = pd.DataFrame()
	df_sum_term = pd.DataFrame()
	df_sum_nov = pd.DataFrame()
	df_sum_broker = pd.DataFrame()

	slice_num = 1
	cumulative_rows = 0

	while run_dt == date.today():
		try:
			url = url_base + run_dt.strftime("%Y_%m_%d_") + str(slice_num) +\
					".zip"
			print url
			df = pd.read_csv(url, compression="zip")
			df_asw, df_trade, df_term, df_nov, df_broker = filter_SDR(df)

			df_sum_trade = df_sum_trade.append(df_trade)
			df_sum_asw = df_sum_asw.append(df_asw)
			df_sum_term = df_sum_term.append(df_term)
			df_sum_nov = df_sum_nov.append(df_nov)
			df_sum_broker = df_sum_broker.append(df_broker)

			current_rows = df_sum_asw.index.size +\
							df_sum_trade.index.size +\
							df_sum_term.index.size +\
							df_sum_nov.index.size +\
							df_sum_broker.index.size

			if current_rows > cumulative_rows:
				#...then new trades were recorded
				#1) save them to file
				df_sum_trade.to_csv("SDR_trade.csv")
				df_sum_asw.to_csv("SDR_asw.csv")
				df_sum_term.to_csv("SDR_term.csv")
				df_sum_nov.to_csv("SDR_nov.csv")
				df_sum_broker.to_csv("SDR_broker.csv")
				#2) call function to email them out
				send_email(["SDR_trade.csv",
							"SDR_asw.csv",
							"SDR_term.csv",
							"SDR_nov.csv",
							"SDR_broker.csv"],
							run_dt)

				#df_sum_trade.to_pickle("SDR_RT_trade.pkl")

			cumulative_rows = current_rows
			slice_num += 1
		except:
			print "Sleeping while waiting for slice #: " + str(slice_num)
			time.sleep(60)		#sleeps for 60 seconds

	return 0

def run_EOD(run_dt):
	"""runs EOD report"""
	url_base = "https://kgc0418-tdw-data2-0.s3.amazonaws.com/slices/CUMULATIVE_RATES_"

	url = url_base + run_dt.strftime("%Y_%m_%d") + ".zip"
	df = pd.read_csv(url, compression="zip")

	df_asw, df_trade, df_term, df_nov, df_broker = filter_SDR(df)

	df_trade.to_csv("SDR_trade.csv")
	df_asw.to_csv("SDR_asw.csv")
	df_term.to_csv("SDR_term.csv")
	df_nov.to_csv("SDR_nov.csv")
	df_broker.to_csv("SDR_broker.csv")
	#2) call function to email them out
	send_email(["SDR_trade.csv",
				"SDR_asw.csv",
				"SDR_term.csv",
				"SDR_nov.csv",
				"SDR_broker.csv"],
				run_dt)

	return df, df_trade, df_asw

if __name__ == "__main__":

	run_dt = date.today()
	run_RT(run_dt)
	#run_dt = date(2019,02,15)
	#df, df_trade, df_asw = run_EOD(run_dt)
