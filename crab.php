<?php
/*
    CRAB script by Ole-Henrik Jakobsen

    This script use phpTempReader to get the measurments and send them to a website.
    It can also use phpGPSReader to send the location data.
    
    For a pure CLI script, use "php ./crab-cli.php" instead.
    
    This script will limit number of inputs to 2 sensors, which is the maximum for the website it will be posted to.
    One sensor should be placed in the water, and the other (which is optional) should be placed on land in the shadow.
    It's a good idea to mark them properly with eg. colored tie wrap.
    Accepted measurment units is limited to C (Celcius) and F (Farenheit).
    
    You will need a key to be able to upload your data, please register an account at https://crab.today
    
    The configuration for this script is crab.ini
    
    Requirements: php-cli, php-curl, phpTempReader
    Optional: phpGPSReader
    
    Last updated: 2022-08-08
*/

// get variables from the configuration file and parse it
$ini_file = "crab.ini";
$ini_array = parse_ini_file($ini_file);

// put array data into variables
$cli_argv = (isset($_SERVER["argv"][1]) ? $_SERVER["argv"][1] : null);
$key = (isset($ini_array["KEY"]) ? $ini_array["KEY"] : null);
$crabtest = (isset($ini_array["TEST"]) ? $ini_array["TEST"] : null);
$connwait = (isset($ini_array["CONNECTION_WAIT"]) ? $ini_array["CONNECTION_WAIT"] : 10);
$tempr_path = (isset($ini_array["TEMPREADER_PATH"]) ? $ini_array["TEMPREADER_PATH"] : null);
$use_sensor = (isset($ini_array["TEMPREADER_SENSOR"]) ? $ini_array["TEMPREADER_SENSOR"] : null);
$gps_path = (isset($ini_array["GPSREADER_PATH"]) ? $ini_array["GPSREADER_PATH"] : null);
$lat = (isset($ini_array["GPS_FALLBACK"]) ? (isset($ini_array["LATITUDE"]) ? $ini_array["LATITUDE"] : null) : null);
$long = (isset($ini_array["GPS_FALLBACK"]) ? (isset($ini_array["LONGITUDE"]) ? $ini_array["LONGITUDE"] : null) : null);
$cusfile = (isset($ini_array["CUSTOM_FILE"]) ? $ini_array["CUSTOM_FILE"] : null);
$imgfile = (isset($ini_array["WEBCAM_FILE"]) ? $ini_array["WEBCAM_FILE"] : null);
$temp = 0;
$unit = "";

$host = "send.crab.today";
$port = 443;

// check the key
if($crabtest && !preg_match("/^([a-zA-Z0-9_-]{32})$/", $key)) {
	die("\nInvalid key, check if you have the correct key and try again.\n");
}

if($cli_argv != "log") {
	// run TempReader if set
	if($tempr_path && is_file("" . $tempr_path . "/tempreader.php")) {
		chdir($tempr_path);
		include_once("" . $tempr_path . "/tempreader.php");
		
		$tempreader = tempreader(1); // 1 = get separate arrays
		if(!is_array($tempreader)) { die("No temperature data received. Check your configuration."); }
		
		if(!$use_sensor) { $use_sensor = key($tempreader); }
		
		$unit = $tempreader[$use_sensor]["unit"];
		$temp_str = $tempreader[$use_sensor]["temperature"];
		$serial_str = $tempreader[$use_sensor]["serialnumber"];
		
		$temp = implode(";", $temp_str);		// We can include all temperatures and sensors using implode().
		$serial = implode(";", $serial_str);		// We can include all sensor serial numbers using implode().
								// We only accept max two sensors anyway: one for the water and one for the air. Define the sensor(s) on the webpage.
								// Only the two first sensors will be accepted, only one is mandatory. Rest will be ignored.
	}

	// run GPSReader if set
	if($gps_path && is_file("" . $gps_path . "/gpsreader.php")) {
		chdir($gps_path);
		include_once("" . $gps_path . "/gpsreader.php");
		
		$gpsreader = gpsreader();
		
		$latitude = $gpsreader["latitude"];
		$longitude = $gpsreader["longitude"];
		
		if(preg_match('/^[-]?(([0-8]?[0-9])\.(\d+))|(90(\.0+)?)$/', $latitude) && preg_match('/^[-]?((((1[0-7][0-9])|([0-9]?[0-9]))\.(\d+))|180(\.0+)?)$/', $longitude)) {
			$lat = $latitude;
			$long = $longitude;
		}
		
		if(!$lat && !$long) { die("No location data received.\n"); }
	}
}

if(!$crabtest) {
	$timeout = $connwait*60; // $min*60s
	$fp = fsockopen('ssl://'.$host,$port,$errno,$errstr,$timeout);
	if(!$fp) {
		die("Could not open a connection to $host\n");
	}
	fclose($fp);
	
	$url = "https://" . $host . "";
	
	if($cli_argv == "log") {
		$serial = "__log";
	}
	
	$post = array('key'    => $key,
			'lat'    => $lat,
			'long'   => $long,
			'temp'   => $temp,
			'serial' => $serial,
			'unit'   => $unit
	);
	
	if($cusfile) {
		$post['custom'] = file_get_contents($cusfile, false, NULL, 0, 384);
	}
	
	if($imgfile) {
		// very basic checking for mimetype after extension, the real deal happens serverside anyway.
		if(stristr($imgfile, 'png')) {
			$mimetype = "image/png";
		}
		else {  $mimetype = "image/jpeg"; }
		$post['image'] = curl_file_create($imgfile, $mimetype, $key);
	}
	
	// create a new cURL resource
	$ch = curl_init();
	
	// set URL and other appropriate options
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
	
	// grab URL and pass it to the browser
	curl_exec($ch);
	
	// close cURL resource, and free up system resources
	curl_close($ch);
}
else {
	$name_script_error = "";
	if(!@$tempreader && $tempr_path) {
		$name_script_error = "phpTempReader";
	}
	else if(!@$gpsreader && $gps_path) {
		$name_script_error = "phpGPSReader";
	}
	else {
		$name_script_error .= "CRAB TEST MODE: Check your data if it looks OK, before you disable test mode in the configuration file.\n\n";
		$name_script_error .= "KEY: $key\n";
		$name_script_error .= "LATITUDE: $lat\n";
		$name_script_error .= "LONGITUDE: $long\n";
		$name_script_error .= "TEMPERATURE: $temp\n";
		$name_script_error .= "SERIAL: $serial\n";
		$name_script_error .= "UNIT: $unit\n";
		if($cusfile) {
			$name_script_error .= file_get_contents($cusfile, false, NULL, 0, 384);
		}
		die($name_script_error);
	}
	
	die("\nCRAB Error: no valid information received from $name_script_error. Check if it is running in test mode.\n");
}
?>
