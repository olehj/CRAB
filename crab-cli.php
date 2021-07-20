<?php
/*
    CRAB CLI script by Ole-Henrik Jakobsen
    
    This script will limit number of inputs to 2 sensors, which is the maximum for the website it will be posted to.
    One sensor should be placed in the water, and the other (which is optional) should be placed on land in the shadow.
    It's a good idea to mark them properly with eg. colored tie wrap.
    Accepted measurment units is limited to C (Celcius) and F (Farenheit).
    
    You will need a key to be able to upload your data, please register an account at https://crab.today
    
    Requirements: php-cli, php-curl
    
    Last updated: 2020-04-15
*/

// get variables from the configuration file and parse it
// put array data into variables

$host = "send.crab.today";	// Set the hostname where to send the data to
$port = 443;			// Set the port for the hostname
$connwait = 10;			// Wait [num] minutes until connection failure

// print help text if nothing or "help" is issued.
if($argc === 1 || preg_match("/^(.*)help(.*)$/i", $argv[1])) {
die("_______________________________________________________________________________
CRAB help

Usage:
  php crab.php [options]

Options:
  API key: (required)
    key     Set the API key for CRAB

  Temperature sensor(s): (required)
    temp    Send the temperature measured in format: 
            [-]XX.XXX[,[-]XX.XXX] (second sensor is optional).

    serial  Set a unique serial name per temp sensor. If none is available,
            make up one like 'water' and 'air' etc. Allowed characters:
              upto 32 characters of: a-z A-Z 0-9 - _ .
            The serial name should not be changed after first executed report,
            as you will need to reconfigure the sensors in CRAB and
            earlier reported data will be unaccessible (but not deleted).
            Create a new API key with new sensors instead.

    unit    Specify if the temperature is in
            [C]elcius or [F]arenheit.

  GPS Location sensor: (required)
    loc     Send the GPS latitude and longitude in decimal format:
            [lat,long]: [-]XX.XXXXX,[-]XX.XXXXX

  Custom data: (optional)
    custom  Send custom data from FILE to store on CRAB logs page.
            No formatting available, only pure text with line breaks.
            Max 256 characters long.

  Image capture: (optional)
    image   Send an image to the server, specfy the file with full path.
            Supports only JPEG and PNG images, max. 10MB (1200x800).

Examples:
  One temperature sensor and custom:
    php crab.php \
      key=FOOFOOFOOFOOFOOFOOFOOFOOFOOFOOFO \
      temp=22.545 \
      serial=53n50r-1337 \
      unit=C \
      loc=-10.00000,50.00000 \
      custom=/home/crab/customdata.txt
    
  Two temperature sensors and an image:
    php crab.php \
      key=FOOFOOFOOFOOFOOFOOFOOFOOFOOFOOFO \
      temp=22.545,31.337 \
      serial=53n50r-1337,s3n50r-31337 \
      unit=C \
      loc=-10.00000,50.00000
      image=/home/crab/image.png
    
    Mark that first sensor will match the first serial number,
    and second will match the second.

  Use commas [,] for separation.
_______________________________________________________________________________
https://crab.today/                                          support@crab.today

");
}
else {
	// create an array with our data
	for($i=1;$i<$argc;$i++) { //skip first argv as it just contains this filename $i=1
		list($arr_key, $arr_val) = explode('=', $argv[$i]);
		$arg_array[$arr_key] = $arr_val;
	}
	
	// defining and adjusting variables
	$key = (isset($arg_array["key"]) ? $arg_array["key"] : null);
	$temp = (str_replace(",", ";", isset($arg_array["temp"])) ? $arg_array["temp"] : null);
	$serial = (str_replace(",", ";", isset($arg_array["serial"])) ? $arg_array["serial"] : null);
	$unit = (isset($arg_array["unit"]) ? $arg_array["unit"] : null);
	$loc = (isset($arg_array["loc"]) ? $arg_array["loc"] : null);
	$custom = (isset($arg_array["custom"]) ? $arg_array["custom"] : null);
	$imgfile = (isset($arg_array["image"]) ? $arg_array["image"] : null);
	$lat = "";
	$long = "";
	
	// split location data
	if($loc) {
		list($lat, $long) = explode(",", $loc);
	}
	
	// check if we can connect before we continue
	$timeout = $connwait*60; // $min*60s
	$fp = fsockopen('ssl://'.$host,$port,$errno,$errstr,$timeout);
	if(!$fp) {
		die("Could not open a connection to $host\n");
	}
	fclose($fp);
	
	// setup POST URI
	$url = "https://" . $host . "";
	
	// setup POST array
	$post = array('key'    => $key,
			'lat'    => $lat,
			'long'   => $long,
			'temp'   => $temp,
			'serial' => $serial,
			'unit'   => $unit
	);
	
	if($custom) {
		$post['custom'] = file_get_contents($custom, false, NULL, 0, 384);
	}
	
	// if an image is supplied, add this into the array as well
	if($imgfile) {
		// very basic checking for mimetype after extension, the real deal happens serverside anyway.
		if(stristr($imgfile, 'png')) {
			$mimetype = "image/png";
		}
		else {  $mimetype = "image/jpeg"; }
		// create the file for POST
		$post['image'] = curl_file_create($imgfile, $mimetype, $key);
	}
	
	// create a new cURL resource
	$ch = curl_init();
	
	// set URL and POST options
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
	
	// grab URL and pass it to the browser
	curl_exec($ch);
	
	// close cURL resource, and free up system resources
	curl_close($ch);
}
?>
