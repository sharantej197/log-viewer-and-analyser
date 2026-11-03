BEGIN{
    FS=" "
    OFS=" "
    RS="\n"
    output = "true"
}

{
    if ($0 !~ /^\[[A-Z][a-z]{2} [A-Z][a-z]{2} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}\] \[(notice|error|warn)\] .*$/) {
            output="false"
    }
}

END{
    print output;
}
