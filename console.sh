#!/usr/bin/env bash

SERVER=${1:-http://localhost:8080}
TOKENID='564321ad-0eb8-4398-ad5d-723afa1d0fb7'
USERID='aaf5d3a4-3465-46e8-b356-74cb158231e8'
ACSID='5429e4d35b6e911769028f8d'
DRIVERID=''
PASSENGERID=''

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
            data="token=${TOKENID}"
            data="$data&car_color=red"
            data="$data&license_plate=LU123HA"
            data="$data&telephone=3282935718"
            location=$(gimmeurjson ${SERVER}/1/drivers/add POST "$data")
            echo ${location}
            DRIVERID=$(echo $location | cut -d/ -f 6)
            ;;
        *)
            wtf
        esac
        ;;
    dr)
        shift
        case $1 in
        a)
            data="token=${TOKENID}"
            if [ -n "$DRIVERID" ]; then
                data="$data&driver_id=${DRIVERID}"
            else
                data="$data&passenger_id=${PASSENGERID}"
            fi
            gimmeurjson ${SERVER}/1/drive_requests/active GET "$data"
            ;;
        *)
            wtf
        esac
        ;;
    p)
        shift
        case $1 in
        u)
            shift
            gimmeurjson ${SERVER}/1/passengers/unmatched GET "token=${TOKENID}&$@"
            ;;
        a)
            shift
            data="token=${TOKENID}"
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
            data="token=${TOKENID}"
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
            data="token=${TOKENID}"
            gimmeurjson ${SERVER}/1/users/${USERID}/view GET "$data"
            ;;
        l)
            data="acs_id=${ACSID}"
            data="$data&facebook_token=${FACEBOOKTOKEN}"
            gimmeurjson ${SERVER}/1/users/login POST "$data"
            ;;
        a)
            shift
            case $1 in
            pc)
                data="token=${TOKENID}"
                data="$data&name=TUTTIBRIAI15"
                gimmeurjson ${SERVER}/1/users/${USERID}/activate/promo_code POST "$data"
                ;;
            *)
                wtf
            esac
            ;;
        *)
            wtf
        esac
        ;;
    f)
        shift
        case $1 in
        a)
            data="token=${TOKENID}"
            data="$data&user_id=${USERID}"
            data="$data&message=Fa caa"
            gimmeurjson ${SERVER}/1/feedbacks/add POST "$data"
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
