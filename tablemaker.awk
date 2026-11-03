BEGIN{
    FS=" "
    OFS=","
    RS="\r|\n|\r\n|\n\r"
    ORS="\r\n"
}
{   gsub(/\[|\]/,"",$0)
    time=$1" "$2" "$3" "$4" "$5;
    if($0 ~ /workerEnv\.init\(\) ok .*$/){
        print NR,time,$6,$7" "$8" "$9",E2";

    } else if($0 ~ /mod_jk child workerEnv in error state .*$/){
        print NR,time,$6,"mod_jk child workerEnv in error state "$13",E3";

    } else if($0 ~ /jk2_init\(\) Found child [0-9]+ in scoreboard slot [0-9]+/){
        print NR,time,$6,"jk2_init() Found child "$10" in scoreboard slot "$14",E1";

    } else if($0 ~ /Directory index forbidden by rule:.*/){
        print NR,time,$6,$7" "$8" Directory index forbidden by rule: "$14",E4";

    } else if($0 ~ /jk2_init\(\) Can't find child [0-9]+ in scoreboard/){
        print NR,time,$6,"jk2_init() Can't find child "$11" in scoreboard slot "",E5";

    } else if($0 ~ /mod_jk child init .*/){
        print NR,time,$6,"mod_jk child init "$10" "$11",E6";

    } else if($0 ~ /script not found or unable to stat/){

    } else{
        rec=$0
        gsub(time" "$6" ","",rec)
        gsub(/,/, "", rec)
        print NR,time,$6,rec,"";

    }
}
