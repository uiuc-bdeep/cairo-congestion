# clear workspace

rm(list = ls())

# set working directory

setwd("/home/bdeep/share/projects/Cairo/test/")

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
              "ggmap",
              "ggplot2")

lapply(packages, pkgTest)

# input

test.path <- "cairo-congestion.csv"

# read data 

test <- read.csv(test.path, header = TRUE)

coords <- as.data.frame(str_split_fixed(test$origin, ",", 2))
coords$V1 <- as.numeric(as.character(coords$V1))
coords$V2 <- as.numeric(as.character(coords$V2))

# plot map of origin points

Cairo <- c(long = 31.35, lat = 30.044444)
Cairo_map <- get_map(location = Cairo, maptype = "satellite", source = "google", zoom = 11)

ggmap(Cairo_map) + geom_point(data = coords, aes(y = V1, x = V2))

ggsave("origins.png", height = 5, width = 8, dpi = 300)

# plot distribution of travel times

# convert to minutes

test$duration.driving. <- test$duration.driving. / 60

ggplot(test) +
  geom_histogram(aes(duration.driving.), binwidth = 1) +
  ggtitle("Cairo Crawler Test", subtitle = "100 Trips") + 
  xlab("Duration (Minutes)") +
  ylab("Number of Trips") +
  theme_bw() 

ggsave("distribution.png", height = 5, width = 8, dpi = 300)

# plot distribution of travel times over the course of the day


# group data according to time of departure

test <- group_by(test, cairo_time)

test1 <- summarise(test, mean = mean(duration.driving.), sd = sd(duration.driving))

# create confidence intervals 

test1$ci1 <- test1$mean + 1.96 * test1$sd
test1$ci2 <- test1$mean - 1.96 * test1$sd

# plot

ggplot(test1) + 
  geom_point(aes(y = mean, x = cairo_time)) +
  geom_line(aex(y = mean, x = cairo_time)) +
  geom_errorbar(aes(ymin = ci2, ymax = ci1), width = 0.1) + 
  xlab("Time of Day") + ylab("Average Duration") +
  ggtitle("Crawler Test Run", subtitle = "100 trips crawled 12 times") + 
  theme_bw()
  
ggsave("time-of-day.png", height = 5, width = 8, dpi = 300)

# regress travel times on time of day with trip FEs


