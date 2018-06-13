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
              "lfe",
              "lubridate",
              "stringr",
              "ggmap",
              "ggplot2")

lapply(packages, pkgTest)

# input

# data from latest test run of crawler

test.path <- "cairo-congestion-20180613.csv"

# read data 

test <- read.csv(test.path, header = TRUE)

# generate background map of Cairo with satellite imagery

Cairo <- c(long = 31.2357, lat = 30.044444)
Cairo_map <- get_map(location = Cairo, maptype = "roadmap", source = "google", zoom = 10)

# plot map of origin points

ggmap(Cairo_map) + 
  ggtitle("Test Run 06/08/2018 - 06/13/2018") +
  geom_point(aes(y = origin_lat, x = origin_long), size = 0.7, color = "blue",data = test) +
  theme(axis.ticks = element_blank(),
        axis.text = element_blank(),
        axis.title = element_blank())

ggsave("origins.png", height = 5, width = 8, dpi = 300)

# plot distribution of travel times

# convert to minutes

test$driving_duration_in_traffic <- test$driving_duration_in_traffic / 60

ggplot(test) +
  geom_histogram(aes(driving_duration_in_traffic), binwidth = 1) +
  ggtitle("Cairo Crawler Test", subtitle = "Test Run 06/08/2018 - 06/13/2018") + 
  xlab("Duration (Minutes)") +
  ylab("Number of Trips") +
  theme_bw() 

ggsave("distribution.png", height = 5, width = 8, dpi = 300)

# plot distribution of travel times over the course of the day

# group data according to time of departure

test <- group_by(test, cairo_time)

test1 <- summarise(test, 
                   mean = mean(driving_duration_in_traffic), 
                   sd = sd(driving_duration_in_traffic))

# create confidence intervals 

test1$ci1 <- test1$mean + 1.96 * test1$sd
test1$ci2 <- test1$mean - 1.96 * test1$sd

# format time of day variable 

test1$cairo_time <- format(test1$cairo_time, format = "%H:%M:%S")
test1$cairo_time <- as.POSIXct(test1$cairo_time, format = "%H:%M:%S")

# plot

ggplot() + 
    geom_line(mapping = aes(x = cairo_time, y = mean), data = test1) +
    geom_point(mapping = aes(x = cairo_time, y = mean), data = test1) +
    xlab("Time of Day") + ylab("Average Duration /n (Minutes)") +
    ggtitle("Average Duration Over Time", "Test Run 06/08/2018 - 06/13/2018") + 
    theme_bw()
  
ggsave("time-of-day.png", height = 5, width = 8, dpi = 300)

# generate trip IDs

trips <- as.data.frame(cbind(test$origin_lat, test$origin_long, test$destination_lat, test$destination_long))
trips <- unique(trips)
trips$trip_id <- seq.int(nrow(trips))

names(trips)[names(trips) == "V1"] <- "origin_lat"
names(trips)[names(trips) == "V2"] <- "origin_long"
names(trips)[names(trips) == "V3"] <- "destination_lat"
names(trips)[names(trips) == "V4"] <- "destination_long"

# merge 

test <- merge(test, trips, by = c("origin_lat", "origin_long", "destination_lat", "destination_long"), all.x = TRUE)

# regress travel times on time of day with trip FEs

test$cairo_time <- as.factor(test$cairo_time)

m1 <- felm(driving_duration_in_traffic ~ cairo_time | trip_id, data = test) 

coef <- as.data.frame(summary(m1)$coefficients)

coef <- cbind(test1$cairo_time[2:102], coef)
names(coef)[names(coef) == "test1$cairo_time[2:102]"] <- "cairo_time"

coef$cairo_time <- format(coef$cairo_time, format = "%H:%M:%S")
coef$cairo_time <- as.POSIXct(coef$cairo_time, format = "%H:%M:%S")

coef$ci1 <- coef$Estimate - 1.96 * coef$`Std. Error`
coef$ci2 <- coef$Estimate + 1.96 * coef$`Std. Error`

# plot

ggplot() + 
  ggtitle("Regress duration on time of day",
          subtitle = "with Trip FEs, Test Run 06/08/2018 - 06/13/2018") +
  ylab("Estimate") +
  xlab("Time of Day") +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), data = coef) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef, alpha = 0.5) +
  theme_bw()

ggsave("estimate.png", height = 5, width = 8, dpi = 300)



