#!/usr/bin/env bash

SERVER=${1:-http://localhost:8080}
TOKENID='e1bbdb07-2330-40e9-a3a5-9f09e9bdf4b3'
USERID='aaf5d3a4-3465-46e8-b356-74cb158231e8'

parse_json() {
    local json

    read json
    echo ${json} | python -mjson.tool | pygmentize -l javascript
}

parse_location() {
    local location

    read location
    echo ${location}
}

parse_header() {
    local header

    read header
    if [ "${header}" == "HTTP/1.1 200 OK" ]; then
        parse_json
    else 
        echo ${header}
        if [ "${header}" == "HTTP/1.1 201 Created" ]; then
            parse_location
        fi
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
    destinations)
        shift
        case $1 in
        list)
            shift
            gimmeurjson ${SERVER}/1/destinations GET "token=tid&$@"
            ;;
        predefined)
            shift
            gimmeurjson ${SERVER}/1/destinations/predefined GET "token=tid&$@"
            ;;
        *)
            wtf
        esac
        ;;
    drivers)
        shift
        case $1 in
        add)
            shift 
            gimmeurjson ${SERVER}/1/drivers/add POST "token=tid&$@"
            ;;
        accepted_passengers)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${id}/accepted_passengers GET "token=tid&$@"
            ;;
        view)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${id}/view GET "token=tid&$@"
            ;;
        edit)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${id}/edit POST "token=tid&$@"
            ;;
        hide)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${id}/hide POST "token=tid&$@"
            ;;
        unhide)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${id}/unhide POST "token=tid&$@"
            ;;
        accept_passenger)
            local did pid

            shift; did=$1; shift; pid=$1; shift
            gimmeurjson ${SERVER}/1/drivers/${did}/accept/passenger/${pid} POST "token=tid&$@"
            ;;
        *)
            wtf
        esac
        ;;
    drive_requests)
        shift
        case $1 in
        list_active)
            shift
            gimmeurjson ${SERVER}/1/drive_requests/active GET "token=tid&$@"
            ;;
        *)
            wtf
        esac
        ;;
    p)
        shift
        case $1 in
        list_unmatched)
            shift
            gimmeurjson ${SERVER}/1/passengers/unmatched GET "token=${TOKENID}&$@"
            ;;
        a)
            shift
            data="token=${TOKENID}"
            data="$data&destination=Bar Eden"
            data="$data&destination_latitude=44.86937"
            data="$data&destination_longitude=10.24324"
            data="$data&origin=Via Mazzini"
            data="$data&origin_latitude=43.87272"
            data="$data&origin_longitude=10.25022"
            data="$data&seats=1"
            echo $data
            gimmeurjson ${SERVER}/1/passengers/add POST "token=${TOKENID}&$data"
            ;;
        view)
            local id

            shift; id=$1; shift
            gimmeurjson ${SERVER}/1/passengers/${id}/view GET "token=tid&$@"
            ;;
        accept_driver)
            local did pid

            shift; pid=$1; shift; did=$1; shift
            gimmeurjson ${SERVER}/1/passengers/${pid}/accept/driver/${did} POST "token=tid&$@"
            ;;
        alight)
            local pid

            pid='943234b5-6c6c-4295-a087-edb57b620184'
            gimmeurjson ${SERVER}/1/passengers/${pid}/alight POST "token=0e72af34-ef53-4540-8ff6-6b935b5c4881"
            ;;
        calculate_fare)
            shift
            gimmeurjson ${SERVER}/1/passengers/calculate_fare GET "token=${TOKENID}&$@"
            ;;
        *)
            wtf
        esac
        ;;
    users)
        shift
        case $1 in
        view)
            local id

            shift; id=$1; shift
            #gimmeurjson ${SERVER}/1/users/${id}/view GET "token=tid&$@"
            gimmeurjson ${SERVER}/1/users/${USERID}/view GET "token=${TOKENID}&$@"
            ;;
        login)
            shift
            gimmeurjson ${SERVER}/1/users/login POST "$@"
            ;;
        *)
            wtf
        esac
        ;;
    feedbacks)
        shift
        case $1 in
        add)
            shift
            gimmeurjson ${SERVER}/1/feedbacks/add POST "token=${TOKENID}&user_id=${USERID}&$@"
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
