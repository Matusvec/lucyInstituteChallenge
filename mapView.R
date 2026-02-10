# Mark's Vizualization Map of US Opioid Prescriptions by State
---
title: "US_opiod_rx_states"
author: "Mark Chambers"
date: "2026-02-09"
output: html_document
---

```{r setup, include=FALSE, echo=FALSE}
knitr::opts_chunk$set(echo = TRUE)
pacman::p_load(ggplot2, dplyr, tidyverse, data.table, lubridate, ggpubr, skimr, scales, plotly,
               mapproj, stars,
  sf, ggmap, mapview, leaflet, leafsync # for spatial objects and maps
) 


getwd()

list.files("Shape Files")

# read in SQL Draw and US State Shape files

medicaid_vs_nonmedicaid_by_state_by_year = read.csv("medicaid_vs_nonmedicaid_by_state_year.csv")

us_states <- st_read("Shape Files/cb_2018_us_state_20m/cb_2018_us_state_20m.shp")

?left_join

medicaid_by_state_by_year <- us_states %>% 
  left_join(medicaid_vs_nonmedicaid_by_state_by_year,
            by = c("STUSPS" = "state")
  ) %>% 
  group_by(is_medicaid) %>% 
  filter(is_medicaid == "Medicaid")

nonmedicaid_by_state_by_year <- us_states %>% 
  left_join(medicaid_vs_nonmedicaid_by_state_by_year,
            by = c("STUSPS" = "state")) %>% 
  group_by(is_medicaid) %>% 
  filter(is_medicaid == "Non-Medicaid")


m1 <- mapview(medicaid_by_state_by_year, zcol = "total_rx", layer.name = 'total Medicaid rx')
m2 <- mapview(nonmedicaid_by_state_by_year, zcol = "total_rx", layer.name = 'total Non-Medicaid rx')
sync(m1, m2)
