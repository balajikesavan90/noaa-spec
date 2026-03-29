#Deleting all files
rm(list = ls())

gc()

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
library(stringr)
library(lubridate)
library(ggplot2)
library(gridExtra)
library(ggmap)
library(sf)
library(mapview)
library(grid)
library(magick)

# Importing Location Data
IDData <- data.table(read.csv("IDData.csv"))

# Removing Locations that already have charts
LocationList <- IDData[Done == FALSE]

# Randomly picking one of the locations with no chart
set.seed(Sys.time())
LocationList <- LocationList[floor(runif(1, min=1, max=nrow(LocationList)))]

# Pulling ID
id <- LocationList$ID

# Pulling Location metadata
Location <- LocationList$FileName

# Pulling all available data from the location
LocationData <- data.table()
for(year in 1975:(year(now())-1)){
  URL <- paste0("https://www.ncei.noaa.gov/data/global-hourly/access/", year, "/", Location)
  print(year)
  if(curlGetHeaders(URL)[1] != "HTTP/1.1 404 Not Found\r\n"){
    temp <- as.data.table(read.csv(URL))
    tempData <- temp[,c("DATE", "TMP")]
    gc(verbose = FALSE)
    LocationData <- rbind(LocationData, tempData)
    rm(tempData)
  }
}

# Tagging Location ID & formating the data
LocationData$ID <- LocationList[FileName == Location]$ID
LocationData$TMP <- as.character(LocationData$TMP)

# Creating copy of raw data
LocationData_Raw <- LocationData

# Read page 11 of https://www.ncei.noaa.gov/data/global-hourly/doc/isd-format-document.pdf
LocationData$Temperature <- as.numeric(substr(LocationData$TMP, 1, nchar(LocationData$TMP)-2))/10
LocationData$Temperature_DataQuality <- substr(LocationData$TMP, nchar(LocationData$TMP), nchar(LocationData$TMP))
LocationData$Temperature <- case_when(
  LocationData$TMP == "+9999,9" ~ as.numeric(NA),
  LocationData$TMP == "Other" ~ as.numeric(NA),
  !(LocationData$TMP %in% c("+9999,9", "Other")) ~ LocationData$Temperature
)
LocationData$Temperature <- case_when(
  LocationData$Temperature_DataQuality %in% c("0", "1", "4", "5", "9", "A", "C", "I", "M", "P", "R", "U") ~ LocationData$Temperature,
  !(LocationData$Temperature_DataQuality %in% c("0", "1", "4", "5", "9", "A", "C", "I", "M", "P", "R", "U")) ~ as.numeric(NA)
)

# Removing rows with NA
LocationData <- LocationData[complete.cases(LocationData)]

# Extracting Year, Month, Day, Time & Hour
LocationData$Year <- year(as.Date(LocationData$DATE))
LocationData$MonthNum <- month(as.Date(LocationData$DATE))
LocationData$Day <- as.Date(LocationData$DATE)
LocationData$Time <- substr(LocationData$DATE, as.numeric(gregexpr("T", LocationData$DATE))+1, nchar(LocationData$DATE))
LocationData$Hour <- substr(LocationData$Time, 1, 2)

# Aggregating Temperature to Hour
LocationData <- LocationData[, .(Temperature = mean(Temperature)), by = c("ID", "Year", "MonthNum", "Day", "Hour")]

# Filtering the hourly data only for the hour of the day thats populated the most
Best_Hour <- LocationData[, .(x = length(unique(Day))), by = c("Hour")]
Best_Hour <- Best_Hour[order(-x),][1]$Hour
LocationData <- LocationData[Hour == Best_Hour]

# Filtering for Year-Months with atlest 20 days of data
FullMonths <- LocationData[, .(y = length(unique(Day))), by = c("Year", "MonthNum")]
FullMonths <- FullMonths[y >= 20]
FullMonths$y <- NULL
LocationData <- merge(LocationData, FullMonths, by = c("Year", "MonthNum"))

# Filtering for years with data from all months
FullYears <- LocationData[, .(z = length(unique(MonthNum))), by = c("Year")]
LocationData <- LocationData[Year %in% FullYears[z == 12]$Year]

# Tagging Months
LocationData$Month <- case_when(
  LocationData$MonthNum == 1 ~ "JAN",
  LocationData$MonthNum == 2 ~ "FEB",
  LocationData$MonthNum == 3 ~ "MAR",
  LocationData$MonthNum == 4 ~ "APR",
  LocationData$MonthNum == 5 ~ "MAY",
  LocationData$MonthNum == 6 ~ "JUN",
  LocationData$MonthNum == 7 ~ "JUL",
  LocationData$MonthNum == 8 ~ "AUG",
  LocationData$MonthNum == 9 ~ "SEP",
  LocationData$MonthNum == 10 ~ "OCT",
  LocationData$MonthNum == 11 ~ "NOV",
  LocationData$MonthNum == 12 ~ "DEC"
)

# Aggregating Temperature to Month and Year
LocationData_Monthly <- LocationData[, .(avg_Temperature = mean(Temperature)), by = c("ID", "Year", "Month", "MonthNum")]
LocationData_Yearly <- LocationData[, .(avg_Temperature = mean(Temperature)), by = c("ID", "Year")]

# Converting Centigrade to Farenheit
LocationData_Yearly$avg_Temperature_F <- LocationData_Yearly$avg_Temperature * 9/5 + 32
LocationData_Monthly$avg_Temperature_F <- LocationData_Monthly$avg_Temperature * 9/5 + 32

# Converting Month to Factor to ensure Months are orders correctly in ggplot
LocationData_Monthly$Month <- factor(LocationData_Monthly$Month, levels = c("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))

# Pulling first map of location
Map1 <- ggmap(get_map(location = c(lon = LocationList[ID == id]$LONGITUDE, lat = LocationList[ID == id]$LATITUDE), zoom = 6)) +
  geom_point(data = LocationList[ID == id], aes(y = LATITUDE, x = LONGITUDE), shape = 15, color = "red", size = 5) + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        axis.title.y=element_blank(),
        axis.text.y=element_blank(),
        axis.ticks.y=element_blank())

# Pulling second map of location
Map2 <- ggmap(get_map(location = c(lon = LocationList[ID == id]$LONGITUDE, lat = LocationList[ID == id]$LATITUDE), zoom = 3)) +
  geom_point(data = LocationList[ID == id], aes(y = LATITUDE, x = LONGITUDE), shape = 15, color = "red", size = 5) + 
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank(),
        axis.title.y=element_blank(),
        axis.text.y=element_blank(),
        axis.ticks.y=element_blank())

# Combining Maps
FinalMap <- grid.arrange(Map1, Map2, nrow = 1)

# Yearly Centigrade Chart
Yearly_Chart_Centigrade <- ggplot(LocationData_Yearly, aes(Year,avg_Temperature))+
  geom_point(color = "blue", size = 5)+
  theme_bw()+
  annotate("text", x = Inf, y = -Inf, label = "Follow @GraphsAndCharts on Twitter for more",
           hjust=1.1, vjust=-1.1, col="black", cex=10,
           fontface = "bold", alpha = 0.5)+
  geom_smooth(linetype = "dotted", color = "black", se=F)+
  ylab(paste0("Average Temperature (\u00B0C) @ ", as.numeric(Best_Hour), " UTC"))+
  theme(aspect.ratio = .5,
        axis.text.x = element_text(face="bold", size = 20),
        axis.title.x = element_text(face="bold", size = 25),
        axis.text.y = element_text(face="bold", size = 20),
        axis.title.y = element_text(face="bold", size = 25),
        axis.line = element_line(colour = "black"))

# Yearly Farenheit Chart
Yearly_Chart_Farenheit <- ggplot(LocationData_Yearly, aes(Year,avg_Temperature_F))+
  geom_point(color = "blue", size = 5)+
  theme_bw()+ 
  annotate("text", x = Inf, y = -Inf, label = "Follow @GraphsAndCharts on Twitter for more",
           hjust=1.1, vjust=-1.1, col="black", cex=10,
           fontface = "bold", alpha = 0.5)+
  geom_smooth(linetype = "dotted", color = "black", se=F)+
  ylab(paste0("Average Temperature (\u00B0F) @ ", as.numeric(Best_Hour), " UTC"))+
  theme(aspect.ratio = .5,
        axis.text.x = element_text(face="bold", size = 20),
        axis.title.x = element_text(face="bold", size = 25),
        axis.text.y = element_text(face="bold", size = 20),
        axis.title.y = element_text(face="bold", size = 25),
        axis.line = element_line(colour = "black"))

# Monthly Centigrade Chart
Monthly_Chart_Centigrade <- ggplot(LocationData_Monthly, aes(Year,avg_Temperature))+
  geom_point(color = "blue")+
  theme_bw()+
  geom_smooth(linetype = "dotted", color = "black", se=F)+
  facet_wrap(~Month, ncol=3)+
  ylab(paste0("Average Temperature (\u00B0C) @ ", as.numeric(Best_Hour), " UTC"))+
  theme(aspect.ratio = .25,
        axis.text.x = element_text(face="bold", size = 20),
        axis.title.x = element_text(face="bold", size = 25),
        axis.text.y = element_text(face="bold", size = 20),
        axis.title.y = element_text(face="bold", size = 25),
        axis.line = element_line(colour = "black"),
        strip.text = element_text(size=25))

# Monthly Farenheit Chart
Monthly_Chart_Farenheit <- ggplot(LocationData_Monthly, aes(Year,avg_Temperature_F))+
  geom_point(color = "blue")+
  theme_bw()+ 
  geom_smooth(linetype = "dotted", color = "black", se=F)+
  facet_wrap(~Month, ncol=3)+
  ylab(paste0("Average Temperature (\u00B0F) @ ", as.numeric(Best_Hour), " UTC"))+
  theme(aspect.ratio = .25,
        axis.text.x = element_text(face="bold", size = 20),
        axis.title.x = element_text(face="bold", size = 25),
        axis.text.y = element_text(face="bold", size = 20),
        axis.title.y = element_text(face="bold", size = 25),
        axis.line = element_line(colour = "black"),
        strip.text = element_text(size=25))

# Combining Centigrade Image
FinalImage_Centigrade <- grid.arrange(FinalMap, 
                                      Yearly_Chart_Centigrade, 
                                      Monthly_Chart_Centigrade,
                                      ncol = 1, 
                                      nrow = 3,
                                      top = textGrob(paste0(as.character(LocationList[FileName == Location]$NAME), "     Elevation: ", as.character(round(LocationList[FileName == Location]$ELEVATION)), "m"),gp=gpar(fontsize=40,font=3)),
                                      bottom = textGrob("Climate Data sourced from https://www.ncei.noaa.gov/data/global-hourly/access/\nGoogle Map Image sourced using D. Kahle and H. Wickham. ggmap: Spatial Visualization with ggplot2. \nThe R Journal, 5(1), 144-161. URL http://journal.r-project.org/archive/2013-1/kahle-wickham.pdf",gp=gpar(fontsize=25,font=3)))

# Combining Farenheit Image
FinalImage_Farenheit <- grid.arrange(FinalMap, 
                                     Yearly_Chart_Farenheit, 
                                     Monthly_Chart_Farenheit,
                                     ncol = 1, 
                                     nrow = 3,
                                     top = textGrob(paste0(as.character(LocationList[FileName == Location]$NAME), "     Elevation: ", as.character(round(LocationList[FileName == Location]$ELEVATION * 3.28084)), "ft"),gp=gpar(fontsize=40,font=3)),
                                     bottom = textGrob("Climate Data sourced from https://www.ncei.noaa.gov/data/global-hourly/access/\nGoogle Map Image sourced using D. Kahle and H. Wickham. ggmap: Spatial Visualization with ggplot2. \nThe R Journal, 5(1), 144-161. URL http://journal.r-project.org/archive/2013-1/kahle-wickham.pdf",gp=gpar(fontsize=25,font=3)))

# Creating Folder
FolderName <- paste0(as.character(LocationList[FileName == Location]$NAME), " ",as.character(LocationList[FileName == Location]$ELEVATION))
FolderName <- str_replace(FolderName, ", ", "-")
FolderName <- str_replace_all(FolderName, " ", "_")
dir.create(FolderName)

# Outputting all files
# write.csv(LocationData_Raw, paste0(FolderName, "/LocationData_Raw.csv"), row.names = F)
write.csv(LocationData, paste0(FolderName, "/LocationData.csv"), row.names = F)
write.csv(LocationData_Monthly, paste0(FolderName, "/LocationData_Monthly.csv"), row.names = F)
write.csv(LocationData_Yearly, paste0(FolderName, "/LocationData_Yearly.csv"), row.names = F)
ggsave(paste0(FolderName, "/Centigrade.jpeg"), plot = FinalImage_Centigrade, width = 20, height = 30)
ggsave(paste0(FolderName, "/Farenheit.jpeg"), plot = FinalImage_Farenheit, width = 20, height = 30)

# Ensuring this location is not pulled again
IDData$Done <- case_when(
  IDData$ID == id ~ TRUE,
  IDData$ID != id ~ IDData$Done
)
write.csv(IDData, paste0("IDData.csv"), row.names = F)

end <- Sys.time()

end - start