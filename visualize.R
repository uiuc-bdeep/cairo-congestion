# clear workspace

rm(list = ls())

# set working directory

setwd("/home/bdeep/share/projects/Cairo")

# function for loading packages

pkgTest <- function(x)
{
  if (!require(x, character.only = TRUE))
  {
    install.packages(x, dep = TRUE)
    if(!require(x, character.only = TRUE)) stop("Package not found")
  }
}


# load required packages

packages <- c("dplyr",
              "rgdal",
              "ggmap",
              "ggplot2")

lapply(packages, pkgTest)

# input

test.path <- "test/cairo-congestion.csv"

# output

out.path <- "test/"

# read data 

test <- read.csv(test.path, header = TRUE)

coords <- as.data.frame(str_split_fixed(test$origin, ",", 2))
coords$V1 <- as.numeric(as.character(coords$V1))
coords$V2 <- as.numeric(as.character(coords$V2))

# plot map of origin points

Cairo <- c(long = 31.35, lat = 30.044444)
Cairo_map <- get_map(location = Cairo, maptype = "satellite", source = "google", zoom = 11)

ggmap(Cairo_map) + geom_point(data = coords, aes(y = V1, x = V2))

# plot distribution of travel times

# convert to minutes

test$duration.driving. <- test$duration.driving. / 60

ggplot(test) +
  geom_histogram(aes(duration.driving.), binwidth = 1) +
  ggtitle("Cairo Crawler Test", subtitle = "100 Trips") + 
  xlab("Duration (Minutes)") +
  ylab("Number of Trips") +
  theme_bw() 
