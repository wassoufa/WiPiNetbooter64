<?php
// Exercise the installed writer's normalization and serialization without executing the page.
$source=file_get_contents(dirname(__DIR__).'/var/www/html/updatedimms.php');
$start=strpos($source,'if ($defaultgame == "none")');
$end=strpos($source,'if ($opentarget',$start);
$normalize=substr($source,$start,$end-$start);
if (!preg_match('/^\$update = .*;/m',$source,$match)) throw new Exception('Writer expression missing');
foreach(['none','menu','game.bin.gz,generic,none']as$value) {
    $name='Test';$ip='192.0.2.3';$type='Sega Naomi';$opentarget='off';$cab='horizontal';$defaultgame=$value;
    eval($normalize);eval($match[0]);$row=str_getcsv(trim($update),',','"','');
    if(count($row)!==8 || $row[7]!=='horizontal') throw new Exception('Invalid OSM cabinet schema');
}
echo "PASS: OSM, normal game and No Default each retain eight fields\n";
