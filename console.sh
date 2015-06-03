#!/usr/bin/env bash

SERVER=${1:-http://localhost:8080}
PASSENGER_TOKENID='8a575d5d-ca25-4886-906b-3b3505edd2ed'
PASSENGER_USERID='aaf5d3a4-3465-46e8-b356-74cb158231e8'
PASSENGER_ACSID='54d7c6e808c91e0942661cb8'
PASSENGERID=''
DRIVER_TOKENID='c6c65dea-5407-4722-96b2-3b51417d68a9'
DRIVER_USERID='6bbcf285-1be9-4138-a836-9547f1d2082e'
DRIVER_ACSID='54f44d9a54add893dd20cbd2'
DRIVERID=''

parse_json() {
    local json

    read json
    echo ${json} | python -mjson.tool | pygmentize -l javascript
}

parse_location() {
    read location

    echo ${location} | cut -d' ' -f 2
}

parse_header() {
    local header

    read header
    if [ "${header}" == "HTTP/1.1 200 OK" ]; then
        parse_json
    elif [ "${header}" == "HTTP/1.1 201 Created" ]; then
        parse_location
    else
        echo ${header}
    fi
}


gimmeurjson() {
    local url=$1
    local method=${2:-GET}
    local data="$3"
    local line

    [ ${method} = "GET" ] && url="${url}?${data}"

    curl -i -s -w'\n' --header 'Accept: application/json' "${url}" -X "${method}" -d "${data}" |\
    tr -d '\r' |\
    grep -e HTTP -e Location -e \{ |\
    parse_header
}

wtf() {
    echo WTF?!
}

loop() {
    local choice

    read -p '> ' choice
    [ -z "${choice}" ] && {
        return 1
    }
    set ${choice}
    case $1 in
    d)
        shift
        case $1 in
        a)
            data="token=${DRIVER_TOKENID}"
            data="$data&car_color=red"
            data="$data&license_plate=LU123HA"
            data="$data&telephone=3282935718"
            location=$(gimmeurjson ${SERVER}/1/drivers/add POST "$data")
            echo ${location}
            DRIVERID=$(echo $location | cut -d/ -f 6)
            ;;
        hp)
            data="token=${DRIVER_TOKENID}"
            data="$data&latitude=43.8727249"
            data="$data&longitude=10.250217"
            gimmeurjson ${SERVER}/1/drivers/${DRIVERID}/honk/passenger/${PASSENGERID} POST "$data"
            ;;
        *)
            wtf
        esac
        ;;
    dr)
        shift
        case $1 in
        a)
            shift
            case $1 in
            driver)
                data="token=${DRIVER_TOKENID}"
                data="$data&driver_id=${DRIVERID}"
                gimmeurjson ${SERVER}/1/drive_requests/active GET "$data"
                ;;
            passenger)
                data="token=${PASSENGER_TOKENID}"
                data="$data&passenger_id=${PASSENGERID}"
                gimmeurjson ${SERVER}/1/drive_requests/active GET "$data"
                ;;
            *)
                wtf
            esac
            ;;
        *)
            wtf
        esac
        ;;
    i)
        shift
        gimmeurjson ${SERVER}/1/info GET
        ;;
    p)
        shift
        case $1 in
        u)
            data="token=${DRIVER_TOKENID}"
            gimmeurjson ${SERVER}/1/passengers/unmatched GET "$data"
            ;;
        a)
            shift
            data="token=${PASSENGER_TOKENID}"
            data="$data&origin=Via Mazzini, Viareggio"
            data="$data&origin_latitude=43.8727249"
            data="$data&origin_longitude=10.250217"
            data="$data&destination=Bar Eden"
            data="$data&destination_latitude=43.866738"
            data="$data&destination_longitude=10.243564"
            data="$data&seats=1"
            location=$(gimmeurjson ${SERVER}/1/passengers/add POST "${data}")
            echo ${location}
            PASSENGERID=$(echo $location | cut -d/ -f 6)
            ;;
        cf)
            shift
            data="token=${PASSENGER_TOKENID}"
            data="$data&origin_latitude=43.8727249"
            data="$data&origin_longitude=10.250217"
            data="$data&destination_latitude=43.866738"
            data="$data&destination_longitude=10.243564"
            data="$data&seats=1"
            gimmeurjson ${SERVER}/1/passengers/calculate_fare GET "$data"
            ;;
        *)
            wtf
        esac
        ;;
    u)
        shift
        case $1 in
        v)
            shift
            case $1 in
            driver)
                data="token=${DRIVER_TOKENID}"
                gimmeurjson ${SERVER}/1/users/${DRIVER_USERID}/view GET "$data"
                ;;
            passenger)
                data="token=${PASSENGER_TOKENID}"
                gimmeurjson ${SERVER}/1/users/${PASSENGER_USERID}/view GET "$data"
                ;;
            *)
                wtf
                ;;
            esac
            ;;
        a)
            shift
            case $1 in
            pc)
                data="token=${PASSENGER_TOKENID}"
                data="$data&name=TUTTIBRIAI15"
                gimmeurjson ${SERVER}/1/users/${PASSENGER_USERID}/activate/promo_code POST "$data"
                ;;
            *)
                wtf
            esac
            ;;
        u)
            shift
            case $1 in
            p)
                data="token=${PASSENGER_TOKENID}"
                data="$data&latitude=43.8727249"
                data="$data&longitude=10.250217"
                gimmeurjson ${SERVER}/1/users/${PASSENGER_USERID}/update/position POST "$data"
                ;;
            *)
                wtf
            esac
            ;;
        mf)
            shift
            data="token=${PASSENGER_TOKENID}"
            data="$data&with_user=${DRIVER_USERID}"
            gimmeurjson ${SERVER}/1/users/${PASSENGER_USERID}/mutual_friends GET "$data"
            ;;
        *)
            wtf
        esac
        ;;
    f)
        shift
        case $1 in
        a)
            data="token=${PASSENGER_TOKENID}"
            data="$data&user_id=${PASSENGER_USERID}"
            data="$data&message=Fa caa"
            gimmeurjson ${SERVER}/1/feedbacks/add POST "$data"
            ;;
        *)
            wtf
        esac
        ;;
    po)
        shift
        case $1 in
        a)
            data="token=${PASSENGER_TOKENID}"
            data="$data&user_id=${PASSENGER_USERID}"
            gimmeurjson ${SERVER}/1/pois/active GET "$data"
            ;;
        *)
            wtf
        esac
        ;;
    *)
        wtf
    esac
    echo
    return 0
}

while loop; do
    continue
done
