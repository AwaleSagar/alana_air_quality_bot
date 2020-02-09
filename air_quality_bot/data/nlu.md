## intent:greet
- hey
- hello
- hi
- good morning
- good evening
- hey there

## intent:goodbye
- bye
- goodbye
- see you around
- see you later

## intent:affirm
- yes
- indeed
- of course
- that sounds good
- correct

## intent:deny
- no
- never
- I don't think so
- don't like that
- no way
- not really

## intent: air_quality_today
- how [good](good) is the air today
- how [nice](good) is the air today
- how [great](good) is the air today
- how is air quality today
- what are the measures of air quality today

## intent: air_quality_historical
- give me the historical for air quality of the [last](hierarchy_number) [two](number) [months](time_measures)
- give me the historical for air quality of the [last](hierarchy_number) [10](number) [months](time_measures)
- how good was the air quality of the [last](hierarchy_number) [three](number) [years](time_measures)
- how good was the air quality of the [last](hierarchy_number) [4](number) [years](time_measures)
- how was air quality [three](number) [days](time_measures) ago
- was air quality [nice](good) a [week](time_measures)
- how [good](good) air quality was [last](hierarchy_number) [year](time_measures)

## intent: air_quality_forecast
- how [good](good) will air be in [five](number) [weeks](time_measures)
- how [good](good) will air be in [6](number) [weeks](time_measures)
- how [great](good) will air be [next](hierarchy_number) [day](time_measures)
- will air be [great](good) tomorrow
- will we have nice air quality for [next](hierarchy_number) [week](time_measures)
- will air quality be [good](good) in [future](hierarchy_number) [days](time_measures)


## synonym: good
- nice
- great

## regex:number
- [0-9]+
