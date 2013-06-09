#!/usr/bin/env bash


parse_json() {
    local json

    read json
    echo ${json} | python -mjson.tool | pygmentize -l javascript
}

parse_header() {
    local header

    read header
    if [ "${header}" == "HTTP/1.1 200 OK" ]; then
        parse_json
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

    curl -i -s -w'\n' "${url}" -X "${method}" -d "${data}" |\
    tr -d '\r' |\
    sed -n '1p;$p' |\
    parse_header
}

wtf() {
    echo WTF?!
}

loop() {
    local choice

    read -p '> ' choice
    set ${choice}
    case $1 in
    drivers)
        shift
        case $1 in
        list)
            shift
            gimmeurjson http://localhost:8000/1/drivers GET "token=tid&$@"
            ;;
        edit)
            local id

            shift; id=$1; shift
            gimmeurjson http://localhost:8000/1/drivers/${id}/edit POST "token=tid&$@"
            ;;
        *)
            wtf
        esac
        ;;
    passengers)
        shift
        case $1 in
        list)
            shift
            gimmeurjson http://localhost:8000/1/passengers GET "token=tid&$@"
            ;;
        view)
            shift; id=$1
            gimmeurjson http://localhost:8000/1/passengers/${id}/view GET "token=tid&$@"
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
