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
library(data.table)
library(dplyr)
library(BBmisc)

Data <- data.table(read.csv("DataFileList_YEARCOUNT_POST2000.csv"))
Data <- Data[No_Of_Years==20]

LocationList <- as.character(Data$FileName) 

ID <- 0
IDData <- data.table()
for(Location in LocationList){
  ID <- ID+1
  print(ID)
  URL <- paste0("https://www.ncei.noaa.gov/data/global-hourly/access/", "2000", "/", Location)
  if(curlGetHeaders(URL)[1] != "HTTP/1.1 404 Not Found\r\n"){
    temp <- as.data.table(read.csv(URL, nrow = 1))
    tempID <- unique(temp[,c("LATITUDE", "LONGITUDE", "ELEVATION", "NAME")])
    tempID$FileName <- Location
    tempID$ID <- ID
    IDData <- rbind(IDData, tempID)
  }
}

write.csv(IDData,"IDData.csv", row.names = F)

end <- Sys.time()

end - start