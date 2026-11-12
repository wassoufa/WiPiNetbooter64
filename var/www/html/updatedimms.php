<?php
header("Refresh: 1; url=dimms.php");
include 'menu.php';
echo '<html lang="en"><head><meta charset="utf-8"><title>WiPi Netbooter</title>';
echo '<link rel="stylesheet" href="css/sidebarstyles.css">';
echo '<section><center><p>';

$filename = "csv/dimms.csv";
$linenum = $_GET["linenum"];
$action = $_GET["action"];

if ($action == "delete"){
echo 'Deleting '.$_GET["name"].' ...';
echo '</p><center></body></html>';
DelLine($filename, $linenum);
}

if ($action == "update"){
echo 'Updating '.$_GET["name"].' ...';
echo '</p><center></body></html>';
$name = $_GET["name"];
$ip = $_GET["ip"];
$type = $_GET["type"];
$opentarget = $_GET["opentarget"];
$defaultgame = $_GET["defaultgame"];
$cab = $_GET["cab"];
$servermode = file_get_contents('/sbin/piforce/servermode.txt');

if ($defaultgame == "none"){$defaultgame = "none,none,none";}
elseif ($defaultgame == "menu"){$defaultgame = "menu,none,none";}

if ($opentarget == '')
{$opentarget = 'off';}
else{
$filename="csv/dimms.csv";
$string_to_replace=",on,";
$replace_with=",off,";
replace_string_in_file($filename, $string_to_replace, $replace_with);
}

$update = $name.",".$ip.",".$type.",".$opentarget.",".$defaultgame.",".$cab."\n";
UpdateLine($filename, $linenum, $update);

if ($servermode == 'serveron'){
$relaymode = file_get_contents('/sbin/piforce/relaymode.txt');
$zeromode = file_get_contents('/sbin/piforce/zeromode.txt');
$gamearray = explode(",", $defaultgame);

if ($gamearray[0] != 'none' and $gamearray[0] != 'menu'){
$command = escapeshellcmd('sudo python3 /sbin/piforce/wipiloader.py '.$gamearray[0].' '.$ip.' '.$relaymode.' '.$zeromode.' '.$gamearray[1].' '.$gamearray[2]);
$output = shell_exec($command . '> /dev/null 2>/dev/null &');
}

}

}


function DelLine($filename, $linenum){
  
$arr = file($filename);
$lineToDelete = $linenum;
unset($arr["$lineToDelete"]);

if (!$fp = fopen($filename, 'w+')){
        print "Cannot open file ($filename)";
         exit;
    }

if($fp){
    foreach($arr as $line) { fwrite($fp,$line); }
    fclose($fp);
    }

echo "Entry was deleted successfully!";
}

function UpdateLine($filename, $linenum, $update){
  
$arr = file($filename);
$lineToUpdate = $linenum;
$arr["$lineToUpdate"] = $update;

if (!$fp = fopen($filename, 'w+')){
        print "Cannot open file ($filename)";
         exit;
    }

if($fp){
    foreach($arr as $line) { fwrite($fp,$line); }
    fclose($fp);
    }

echo "Entry was updated successfully!";
}

function replace_string_in_file($filename, $string_to_replace, $replace_with){
    $content=file_get_contents($filename);
    $content_chunks=explode($string_to_replace, $content);
    $content=implode($replace_with, $content_chunks);
    file_put_contents($filename, $content);
}

?>