#!/bin/sh

# if this script has died, run it with the command '0 19 * * 1 ./upcoming_house_bills.sh'

# get current year, month, date
# if today is Monday and the file isn't up yet,
# wait 2 hours before retry up to times

# what time is it
year=$(date +"%Y")
month=$(date +"%m")
date=$(date +"%d")

#current_time=20170327
current_time=$year$month$date

# where's the website
house_bills="http://docs.house.gov/floor/Download.aspx?file=/billsthisweek/TIME/TIME.xml"
house_bills_url="${house_bills//TIME/$current_time}"
echo "$house_bills_url"


function get_bills
{
    \curl -vs "$house_bills_url"  2>&1 > ../legis_data/process/house_bills/$current_time.xml
}

# check if today is monday
if [[ $(date '+%a') == "Mon" ]]; then
    echo "alright alright I'm getting it"

    tries=5

    while [ $tries -gt 0 ]
    do
    # go and try to get something
    header=$(get_bills)
    content_type=$(echo "$header" | grep Content-Type)

    # if we get something, then set tries to 1 and peace out
    if [[ $content_type == *"application/x-octet-stream"* ]]; then
        echo "success! We caught something, boys"
        tries=1
    else
        # we have a couple more tries to get through
        echo "whomp whomp whomp"
    fi

    # sleep in between retries
    if [ $tries -gt 1 ]; then
        sleep 7200
    else
        echo "peace out!"
    fi

    # decrement number of tries so we can leave this hellhole
    tries=$[$tries-1]
    done
else
    echo "doing diddly squat"
fi


