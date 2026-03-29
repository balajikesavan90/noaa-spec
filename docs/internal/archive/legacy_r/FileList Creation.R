#Deleting all files
rm(list = ls())

#Clearing the console
cat("\014") 

#Suppressing warnings
options(warn=-1)

#Making sure the output comes in decimal and not scientific
options("scipen"=100, "digits"=7)

#Timing the Code, setting the start time
start <- Sys.time()

#Setting Working Directory
setwd("C:/Users/bkesa1/Documents/Personal/ClimateChange")

#Loading the required libraries
library(rvest)
library(data.table)

YearList1 <- read_html("https://www.ncei.noaa.gov/data/global-hourly/access/")
YearList2 <- html_nodes(YearList1,'td')
YearList3 <- html_text(YearList2)
YearList4 <- YearList3[grepl("/", YearList3)]

DataFileList <- data.table()
for(year in YearList4){
  URL <- paste0("https://www.ncei.noaa.gov/data/global-hourly/access/", year)
  DataFileList1 <- read_html(URL)
  DataFileList2 <- html_nodes(DataFileList1,'td')
  DataFileList3 <- html_text(DataFileList2)
  DataFileList4 <- DataFileList3[grepl(".csv", DataFileList3)]

  temp <- data.table(YEAR = substr(year,1,4),
                     FileName = DataFileList4)
  DataFileList <- rbind(DataFileList, temp)
  print(paste0(year, "DONE!"))
}

write.csv(DataFileList,"DataFileList.csv", row.names = F)

DataFileList_YEARCOUNT_POST2000 <- DataFileList[YEAR>=2000 & YEAR <= 2019, .(No_Of_Years = length(YEAR)), by = "FileName"]
  
write.csv(DataFileList_YEARCOUNT_POST2000,"DataFileList_YEARCOUNT_POST2000.csv", row.names = F)

end <- Sys.time()

end - start
