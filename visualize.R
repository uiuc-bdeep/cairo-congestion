# clear workspace

rm(list = ls())

# set working directory

setwd("/home/bdeep/share/projects/Cairo/test")

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
              "ggplot2",
              "gridExtra")

lapply(packages, pkgTest)
lapply(packages, update.packages)

# input

# data from latest test run of crawler and read data

test <- do.call("rbind", lapply( list.files(path = "./data/", pattern = "*.csv",full=TRUE),
                                 read.csv, header=TRUE))
test$cairo_time[test$cairo_time == "16:00:02"] <- "16:00:00"
test$cairo_time[test$cairo_time == "00:00:01"] <- "00:00:00"

# generate background map of Cairo with satellite imagery

Cairo <- c(long = 31.2357, lat = 30.044444)
Cairo_map <- get_map(location = Cairo, maptype = "roadmap", source = "google", zoom = 10)

# get highway and non-highway data

test[which(test$coord_x == 99),"road_type"] <- "highway"

test[which(test$coord_x != 99),"road_type"] <- "non_highway"

# plot map of origin points

ggmap(Cairo_map) + 
  ggtitle("Test Run 07/16/2018 - 07/22/2018") +
  geom_point(aes(y = origin_lat, x = origin_long, color = test$road_type), size = 0.7, data = test) +
  scale_fill_manual(labels = c("highway", "non_highway"), values = c("blue", "red")) +
  theme(axis.ticks = element_blank(),
        axis.text = element_blank(),
        axis.title = element_blank(),
        legend.position = "right")

ggsave("origins.png", height = 5, width = 8, dpi = 300)

# plot distribution of travel times

# convert to minutes

test$driving_duration_in_traffic <- test$driving_duration_in_traffic / 60

ggplot(test, aes(driving_duration_in_traffic, fill = test$road_type)) +
  geom_histogram(position = "identity", alpha = 0.5, binwidth = 0.1) +
  ggtitle(expression(atop("Cairo Crawler Test", atop("Test Run 07/16/2018 - 07/22/2018")))) +  
  xlab("Duration (Minutes)") +
  ylab("Number of Trips") +
  theme_bw()

ggsave("distribution(combined).png", height = 5, width = 8, dpi = 300)

distribute1 <- ggplot(test[which(test$road_type == "highway"), ]) +
  geom_histogram(aes(driving_duration_in_traffic), color = "blue", binwidth = 1) +
  ggtitle(expression(atop("Cairo Crawler Test", atop("Test Run 07/16/2018 - 07/22/2018"))))+ 
  xlim(0, 80) + ylim(0, 500) +
  xlab("") +
  ylab("Number of Trips(highway)") +
  theme_bw() +
  theme(plot.title = element_text(size = 10),
        #plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 10),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

distribute2 <- ggplot(test[which(test$road_type != "highway"), ]) +
  geom_histogram(aes(driving_duration_in_traffic), color = "red", binwidth = 1) +
  xlim(0, 80) + ylim(0, 1800) +
  xlab("Duration (Minutes)") +
  ylab("Number of Trips(non_highway)") +
  theme_bw() +
  theme(axis.title = element_text(size = 10),
        axis.text = element_text(size = 7))

grid.arrange(distribute1, distribute2, nrow = 2)
distribute <- arrangeGrob(distribute1, distribute2, nrow = 2)
ggsave("distribution.png", distribute, height = 6, width = 5, dpi = 300)

# plot distribution of travel times over the course of the day

# group data according to time of departure
test <- group_by(test, cairo_time)
test_highway <- group_by(test[which(test$road_type == "highway"), ], cairo_time)
test_non_highway <- group_by(test[which(test$road_type != "highway"),], cairo_time)

test1 <- summarise(test, 
                   mean = mean(driving_duration_in_traffic), 
                   sd = sd(driving_duration_in_traffic))

test1_highway <- summarise(test_highway,
                           mean = mean(driving_duration_in_traffic),
                           sd = sd(driving_duration_in_traffic))

test1_non_highway <- summarise(test_non_highway,
                               mean = mean(driving_duration_in_traffic),
                               sd = sd(driving_duration_in_traffic))
# create confidence intervals 

test1$ci1 <- test1$mean + 1.96 * test1$sd
test1_highway$ci1 <- test1_highway$mean + 1.96 * test1_highway$sd

test1_non_highway$ci1 <- test1_non_highway$mean + 1.96 * test1_non_highway$sd
test1$ci2 <- test1$mean - 1.96 * test1$sd

test1_highway$ci2 <- test1_highway$mean - 1.96 * test1_highway$sd
test1_non_highway$ci2 <- test1_non_highway$mean - 1.96 * test1_non_highway$sd

# format time of day variable 

test1$cairo_time <- format(test1$cairo_time, format = "%H:%M:%S")
test1$cairo_time <- as.POSIXct(test1$cairo_time, format = "%H:%M:%S")

test1_highway$cairo_time <- format(test1_highway$cairo_time, format = "%H:%M:%S")
test1_highway$cairo_time <- as.POSIXct(test1_highway$cairo_time, format = "%H:%M:%S")

test1_non_highway$cairo_time <- format(test1_non_highway$cairo_time, format = "%H:%M:%S")
test1_non_highway$cairo_time <- as.POSIXct(test1_non_highway$cairo_time, format = "%H:%M:%S")

# plot 

tday1 <- ggplot() +
  geom_hline(yintercept = mean(test1_highway$mean), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = mean), color = "red", data = test1_highway) +
  geom_point(mapping = aes(x = cairo_time, y = mean), color = "red", data = test1_highway) +
  xlab("") + ylab("Avg Duration /n (Min) \n (highway)") +
  ggtitle(expression(atop("Average Duration Over Time", atop("Test Run 07/16/2018 - 07/22/2018")))) +
  theme_bw() +
  theme(plot.title = element_text(size = 10),
        #plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 10),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

tday2 <- ggplot() + 
  geom_hline(yintercept = mean(test1_non_highway$mean), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = mean), color = "blue", data = test1_non_highway) +
  geom_point(mapping = aes(x = cairo_time, y = mean), color = "blue", data = test1_non_highway) +
  xlab("Time of Day") + ylab("Avg Duration /n (Min) \n (non_highway)") +
  theme_bw() +
  theme(axis.title = element_text(size = 10),
        axis.text = element_text(size = 7))

grid.arrange(tday1,tday2, nrow = 2)
tday <- arrangeGrob(tday1, tday2, nrow = 2)
ggsave("time-of-day.png", tday, height = 6, width = 8, dpi = 300)

## Interpretation: 
# this graph measures during different time of the day, 
# the average number of minustes spent on given trips


# regress travel times on time of day with trip FEs

test$cairo_time <- as.factor(test$cairo_time)
test_highway$cairo_time <- as.factor(test_highway$cairo_time)
test_non_highway$cairo_time <- as.factor(test_non_highway$cairo_time)

m1 <- felm(driving_duration_in_traffic ~ cairo_time | id, data = test)
m1_highway <- felm(driving_duration_in_traffic ~ cairo_time | id, data = test_highway)
m1_non_highway <- felm(driving_duration_in_traffic ~ cairo_time | id, data = test_non_highway)

coef <- as.data.frame(summary(m1)$coefficients)
coef_highway <- as.data.frame(summary(m1_highway)$coefficients)
coef_non_highway <- as.data.frame(summary(m1_non_highway)$coefficients)

# want to bind 'cairo_time' variable from test1 to use as the x-axis
# exclude the first row of test1 so that coef and test1 have the same number of obs.
# n.b. in order to run the regression, felm excludes one value of cairo_time to use as the baseline for comparison

test1 <- test1[-1, ]
test1_highway <- test1_highway[-1, ]
test1_non_highway <- test1_non_highway[-1, ]

coef <- cbind(test1$cairo_time, coef)
names(coef)[names(coef) == "test1$cairo_time"] <- "cairo_time"

coef_highway <- cbind(test1_highway$cairo_time, coef_highway)
names(coef_highway)[names(coef_highway) == "test1_highway$cairo_time"] <- "cairo_time"

coef_non_highway <- cbind(test1_non_highway$cairo_time, coef_non_highway)
names(coef_non_highway)[names(coef_non_highway) == "test1_non_highway$cairo_time"] <- "cairo_time"

coef$cairo_time <- format(coef$cairo_time, format = "%H:%M:%S")
coef$cairo_time <- as.POSIXct(coef$cairo_time, format = "%H:%M:%S")

coef_highway$cairo_time <- format(coef_highway$cairo_time, format = "%H:%M:%S")
coef_highway$cairo_time <- as.POSIXct(coef_highway$cairo_time, format = "%H:%M:%S")

coef_non_highway$cairo_time <- format(coef_non_highway$cairo_time, format = "%H:%M:%S")
coef_non_highway$cairo_time <- as.POSIXct(coef_non_highway$cairo_time, format = "%H:%M:%S")

coef$ci1 <- coef$Estimate - 1.96 * coef$`Std. Error`
coef$ci2 <- coef$Estimate + 1.96 * coef$`Std. Error`

coef_highway$ci1 <- coef_highway$Estimate - 1.96 * coef_highway$`Std. Error`
coef_highway$ci2 <- coef_highway$Estimate + 1.96 * coef_highway$`Std. Error`

coef_non_highway$ci1 <- coef_non_highway$Estimate - 1.96 * coef_non_highway$`Std. Error`
coef_non_highway$ci2 <- coef_non_highway$Estimate + 1.96 * coef_non_highway$`Std. Error`

# no log transformation plot
ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day", atop("with Trip FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  xlab("Time of Day") +
  ylab("Estimate \n (minutes)") +
  geom_hline(yintercept = 0, size = 0.1) +
  geom_hline(yintercept = mean(coef$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), data = coef) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef, alpha = 0.5) 
  theme_bw() 

ggsave("estimate-original.png", height = 4, width = 6, dpi = 300)

est1 <- ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day", atop("with Trips FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  ylab("Estimate \n (Highway)") +
  geom_hline(yintercept = mean(coef_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "red", data = coef_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2) , data = coef_highway, alpha = 0.5) +
  theme_bw() +
  theme(plot.title = element_text(size = 10),
        #plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 10),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

est2 <- ggplot() + 
  ylab("Estimate \n (Non Highway)") +
  xlab("Time of Day") +
  geom_hline(yintercept = mean(coef_non_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "blue", data = coef_non_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef_non_highway, alpha = 0.5) +
  theme_bw() +
  theme(axis.title = element_text(size = 10),
        axis.text = element_text(size = 7))

grid.arrange(est1, est2, nrow = 2)
est <- arrangeGrob(est1, est2, nrow = 2)
ggsave("estimate-original-2.png", est, height = 6, width = 8, dpi = 300)

# plots with log transformation
m1 <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = test)
m1_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = test_highway)
m1_non_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = test_non_highway)

coef <- as.data.frame(summary(m1)$coefficients)
coef_highway <- as.data.frame(summary(m1_highway)$coefficients)
coef_non_highway <- as.data.frame(summary(m1_non_highway)$coefficients)

# want to bind 'cairo_time' variable from test1 to use as the x-axis
# exclude the first row of test1 so that coef and test1 have the same number of obs.
# n.b. in order to run the regression, felm excludes one value of cairo_time to use as the baseline for comparison

coef <- cbind(test1$cairo_time, coef)
names(coef)[names(coef) == "test1$cairo_time"] <- "cairo_time"

coef_highway <- cbind(test1_highway$cairo_time, coef_highway)
names(coef_highway)[names(coef_highway) == "test1_highway$cairo_time"] <- "cairo_time"

coef_non_highway <- cbind(test1_non_highway$cairo_time, coef_non_highway)
names(coef_non_highway)[names(coef_non_highway) == "test1_non_highway$cairo_time"] <- "cairo_time"

coef$cairo_time <- format(coef$cairo_time, format = "%H:%M:%S")
coef$cairo_time <- as.POSIXct(coef$cairo_time, format = "%H:%M:%S")

coef_highway$cairo_time <- format(coef_highway$cairo_time, format = "%H:%M:%S")
coef_highway$cairo_time <- as.POSIXct(coef_highway$cairo_time, format = "%H:%M:%S")

coef_non_highway$cairo_time <- format(coef_non_highway$cairo_time, format = "%H:%M:%S")
coef_non_highway$cairo_time <- as.POSIXct(coef_non_highway$cairo_time, format = "%H:%M:%S")

coef$ci1 <- coef$Estimate - 1.96 * coef$`Std. Error`
coef$ci2 <- coef$Estimate + 1.96 * coef$`Std. Error`

coef_highway$ci1 <- coef_highway$Estimate - 1.96 * coef_highway$`Std. Error`
coef_highway$ci2 <- coef_highway$Estimate + 1.96 * coef_highway$`Std. Error`

coef_non_highway$ci1 <- coef_non_highway$Estimate - 1.96 * coef_non_highway$`Std. Error`
coef_non_highway$ci2 <- coef_non_highway$Estimate + 1.96 * coef_non_highway$`Std. Error`


ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day", atop("with Trip FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  xlab("Time of Day") +
  ylab("Estimate in LogScale \n (minutes)") +
  geom_hline(yintercept = 0, size = 0.1) +
  geom_hline(yintercept = mean(coef$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), data = coef) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef, alpha = 0.5) +
  theme_bw() +
  theme(plot.title = element_text(size = 10),
      #plot.subtitle = element_text(size = 10),
      axis.title = element_text(size = 10),
      axis.text = element_text(size = 7))

ggsave("estimate-log.png", height = 5, width = 8, dpi = 300)


est1 <- ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day", atop("with Trips FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  ylab("Estimate in LogScale \n (Highway)") +
  geom_hline(yintercept = mean(coef_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "red", data = coef_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2) , data = coef_highway, alpha = 0.5) +
  theme_bw() + 
  theme(plot.title = element_text(size = 10),
        #plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 10),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

est2 <- ggplot() + 
  ylab("Estimate in LogScale \n (Non Highway)") +
  xlab("Time of Day") +
  geom_hline(yintercept = mean(coef_non_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "blue", data = coef_non_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef_non_highway, alpha = 0.5) +
  theme_bw() +
  theme(axis.title = element_text(size = 10),
        axis.text = element_text(size = 7))

grid.arrange(est1, est2, nrow = 2)
est <- arrangeGrob(est1, est2, nrow = 2)
ggsave("estimate-log-2.png", est, height = 6, width = 8, dpi = 300)

## Interpretation:
# we regress the unumber of minutes it takes for each trip on the time of the day, each point
# on the line represents on average how many minutes more/less a trip takes compared to 7am
# Is is a measure of how congested the roads are across the course of the day
# this graph shows us that trips on the highway take longer than trips not on the highway

# Check if there is difference between weekends and weekdays
test$week <- weekdays(as.Date(test$cairo_date,'%Y-%m-%d'))
wdays <- test[test$week != c("Sunday", "Saturday"),]
wends <- test[test$week == c("Sunday", "Saturday"),]

m1 <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wdays)
m2 <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wends)

coef1 <- as.data.frame(summary(m1)$coefficients)
coef2 <- as.data.frame(summary(m2)$coefficients)

coef1 <- cbind(test1$cairo_time, coef1)
names(coef1)[names(coef1) == "test1$cairo_time"] <- "cairo_time"
coef2 <- cbind(test1$cairo_time, coef2)
names(coef2)[names(coef2) == "test1$cairo_time"] <- "cairo_time"

coef1$cairo_time <- format(coef1$cairo_time, format = "%H:%M:%S")
coef1$cairo_time <- as.POSIXct(coef1$cairo_time, format = "%H:%M:%S")
coef2$cairo_time <- format(coef2$cairo_time, format = "%H:%M:%S")
coef2$cairo_time <- as.POSIXct(coef2$cairo_time, format = "%H:%M:%S")

coef1$ci1 <- coef1$Estimate - 1.96 * coef1$`Std. Error`
coef1$ci2 <- coef1$Estimate + 1.96 * coef1$`Std. Error`
coef2$ci1 <- coef2$Estimate - 1.96 * coef2$`Std. Error`
coef2$ci2 <- coef2$Estimate + 1.96 * coef2$`Std. Error`


est1 <- ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day", atop("with Trips FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  ylab("Estimate \n Weekdays") +
  geom_hline(yintercept = mean(coef$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "red", data = coef1) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2) , data = coef1, alpha = 0.5) +
  theme_bw() + 
  theme(plot.title = element_text(size = 10),
        #plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 8),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

est2 <- ggplot() + 
  ylab("Estimate \n Weekends") +
  xlab("Time of Day") +
  geom_hline(yintercept = mean(coef2$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate), color = "blue", data = coef2) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2), data = coef2, alpha = 0.5) +
  theme_bw() +
  theme(axis.title = element_text(size = 8),
        axis.text = element_text(size = 7))

grid.arrange(est1, est2, nrow = 2)
est <- arrangeGrob(est1, est2, nrow = 2)
ggsave("estimate_week_log.png", est, height = 5, width = 8, dpi = 300)

# highway vs non-highway on weekdays vs weekends

wdays_highway <- group_by(wdays[which(wdays$road_type == "highway"), ], cairo_time)
wdays_non_highway <- group_by(wdays[which(wdays$road_type != "highway"),], cairo_time)

wends_highway <- group_by(wends[which(wends$road_type == "highway"), ], cairo_time)
wends_non_highway <- group_by(wends[which(wends$road_type != "highway"),], cairo_time)

# regress duration on query time

m1_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wdays_highway)
m1_non_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wdays_non_highway)

m2_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wends_highway)
m2_non_highway <- felm(log(driving_duration_in_traffic) ~ cairo_time | id, data = wends_non_highway)


# save regression output to dataframe

coef1_highway <- as.data.frame(summary(m1_highway)$coefficients)
coef1_non_highway <- as.data.frame(summary(m1_non_highway)$coefficients)

coef2_highway <- as.data.frame(summary(m2_highway)$coefficients)
coef2_non_highway <- as.data.frame(summary(m2_non_highway)$coefficients)

# append x-axis variable (time of day) to regression output

coef1_highway <- cbind(test1_highway$cairo_time, coef1_highway)
names(coef1_highway)[names(coef1_highway) == "test1_highway$cairo_time"] <- "cairo_time"

coef1_non_highway <- cbind(test1_non_highway$cairo_time, coef1_non_highway)
names(coef1_non_highway)[names(coef1_non_highway) == "test1_non_highway$cairo_time"] <- "cairo_time"

coef2_highway <- cbind(test1_highway$cairo_time, coef2_highway)
names(coef2_highway)[names(coef2_highway) == "test1_highway$cairo_time"] <- "cairo_time"

coef2_non_highway <- cbind(test1_non_highway$cairo_time, coef2_non_highway)
names(coef2_non_highway)[names(coef2_non_highway) == "test1_non_highway$cairo_time"] <- "cairo_time"


coef1_highway$cairo_time <- format(coef1_highway$cairo_time, format = "%H:%M:%S")
coef1_highway$cairo_time <- as.POSIXct(coef1_highway$cairo_time, format = "%H:%M:%S")

coef1_non_highway$cairo_time <- format(coef1_non_highway$cairo_time, format = "%H:%M:%S")
coef1_non_highway$cairo_time <- as.POSIXct(coef1_non_highway$cairo_time, format = "%H:%M:%S")

coef2_highway$cairo_time <- format(coef2_highway$cairo_time, format = "%H:%M:%S")
coef2_highway$cairo_time <- as.POSIXct(coef2_highway$cairo_time, format = "%H:%M:%S")

coef2_non_highway$cairo_time <- format(coef2_non_highway$cairo_time, format = "%H:%M:%S")
coef2_non_highway$cairo_time <- as.POSIXct(coef2_non_highway$cairo_time, format = "%H:%M:%S")


# confidence intervals

coef1_highway$ci1 <- coef1_highway$Estimate - 1.96 * coef1_highway$`Std. Error`
coef1_highway$ci2 <- coef1_highway$Estimate + 1.96 * coef1_highway$`Std. Error`

coef1_non_highway$ci1 <- coef1_non_highway$Estimate - 1.96 * coef1_non_highway$`Std. Error`
coef1_non_highway$ci2 <- coef1_non_highway$Estimate + 1.96 * coef1_non_highway$`Std. Error`


coef2_highway$ci1 <- coef2_highway$Estimate - 1.96 * coef2_highway$`Std. Error`
coef2_highway$ci2 <- coef2_highway$Estimate + 1.96 * coef2_highway$`Std. Error`

coef2_non_highway$ci1 <- coef2_non_highway$Estimate - 1.96 * coef2_non_highway$`Std. Error`
coef2_non_highway$ci2 <- coef2_non_highway$Estimate + 1.96 * coef2_non_highway$`Std. Error`

# plot (weekdays)

est1 <- ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day(Weekdays)", atop("with Trips FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  ylab("Estimate in LogScale \n (Highway)") +
  geom_hline(yintercept = mean(coef1_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate, group = 1), color = "red", data = coef1_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2, group = 1) , data = coef1_highway, alpha = 0.5) +
  theme_bw() + 
  theme(plot.title = element_text(size = 10),
        # plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 8),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

est2 <- ggplot() + 
  ylab("Estimate in LogScale \n (Non-Highway)") +
  xlab("Time of Day") +
  geom_hline(yintercept = mean(coef1_non_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate, group = 1), color = "blue", data = coef1_non_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2, group = 1), data = coef1_non_highway, alpha = 0.5) +
  theme_bw() +
  theme(axis.title = element_text(size = 8),
        axis.text = element_text(size = 7))

grid.arrange(est1, est2, nrow = 2)
est <- arrangeGrob(est1, est2, nrow = 2)
ggsave("estimate_wdays.png", est, height = 6, width = 8, dpi = 300)

# plot (weekends)

est1 <- ggplot() + 
  ggtitle(expression(atop("Regress duration on time of day(Weekends)", atop("with Trips FEs, Test Run 07/16/2018 - 07/22/2018")))) +
  ylab("Estimate in LogScale \n (Highway)") +
  geom_hline(yintercept = mean(coef2_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate, group = 1), color = "red", data = coef2_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2, group = 1) , data = coef2_highway, alpha = 0.5) +
  theme_bw() + 
  theme(plot.title = element_text(size = 10),
        # plot.subtitle = element_text(size = 10),
        axis.title.y = element_text(size = 8),
        axis.text = element_text(size = 7),
        axis.title.x = element_blank())

est2 <- ggplot() + 
  ylab("Estimate in LogScale \n (Non-Highway)") +
  xlab("Time of Day") +
  geom_hline(yintercept = mean(coef2_non_highway$Estimate), alpha = 0.5) +
  geom_line(mapping = aes(x = cairo_time, y = Estimate, group = 1), color = "blue", data = coef2_non_highway) + 
  geom_ribbon(mapping = aes(x = cairo_time, ymin = ci1, ymax = ci2, group = 1), data = coef2_non_highway, alpha = 0.5) + 
  theme_bw() 
  theme(axis.title = element_text(size = 8),
        axis.text = element_text(size = 7))

grid.arrange(est1, est2, nrow = 2)
est <- arrangeGrob(est1, est2, nrow = 2)
ggsave("estimate_wends.png", est, height = 6, width = 8, dpi = 300)









