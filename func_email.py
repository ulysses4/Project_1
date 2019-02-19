import matplotlib.pyplot as plt
import numpy as np
import csv

def csv2htmlTableStr(CsvFileName):
    # this function is adapted from
    # https://stackoverflow.com/questions/36856011/convert-csv-to-a-html-table-format-and-store-in-a-html-file
    #
    # Open the CSV file for reading
    reader = csv.reader(open(CsvFileName))

    # initialize rownum variable
    rownum = 0

    # write <table> tag
    HtmlStr = ''
    HtmlStr += '<table>'
    # generate table contents

    for row in reader: # Read a single row from the CSV file

     # write header row. assumes first row in csv contains header
       if rownum == 0:
          HtmlStr += '<tr>' # write <tr> tag
          for column in row:
              HtmlStr += '<th>' + column + '</th>'
          HtmlStr += '</tr>'

      #write all other rows
       else:
          HtmlStr += '<tr>'
          for column in row:
              HtmlStr += '<td>' + column + '</td>'
          HtmlStr += '</tr>'

       #increment row count
       rownum += 1

     # write </table> tag
    HtmlStr += '</table>'

     # print results to shell
    #print "Created " + str(rownum) + " row table."
    return HtmlStr

def rand_plot(file_name):
	rng = np.arange(50)
	rnd = np.random.randint(0, 10, size=(3, rng.size))
	yrs = 1950 + rng

	fig, ax = plt.subplots(figsize=(5, 3))
	ax.stackplot(yrs, rng + rnd, labels=['Eastasia', 'Eurasia', 'Oceania'])
	ax.set_title('Combined debt growth over time')
	ax.legend(loc='upper left')
	ax.set_ylabel('Total debt')
	ax.set_xlim(xmin=yrs[0], xmax=yrs[-1])
	fig.tight_layout()

	plt.savefig(file_name, bbox_inches="tight")

	plt.show()
