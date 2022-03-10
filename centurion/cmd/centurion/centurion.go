package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/hellflame/argparse"
	"github.com/myOmikron/gorcp"
	"io/ioutil"
	"net/http"
	"os"
)

type Config struct {
	RCPSecret    string   `json:"rcp_secret"`
	CenturiaUris []string `json:"centuria_uris"`
	BBBServerUri string   `json:"bbb_server_uri"`
	BBBSecret    string   `json:"bbb_secret"`
}

func main() {
	var config Config
	if dat, err := ioutil.ReadFile("/etc/centurion/config.json"); err != nil {
		fmt.Println(err.Error())
		os.Exit(1)
	} else {
		if err := json.Unmarshal(dat, &config); err != nil {
			fmt.Println(err.Error())
			os.Exit(1)
		}
	}

	rcpConfig := &gorcp.RCPConfig{
		UseTimeComponent: true,
		SharedSecret:     config.RCPSecret,
	}

	parser := argparse.NewParser("centurion", "Commander of bbb-bots", nil)

	attackParser := parser.AddCommand("attack", "Start the attack", nil)
	withdrawParser := parser.AddCommand("withdraw", "Withdraw the attack", nil)

	if err := parser.Parse(nil); err != nil {
		fmt.Println(err.Error())
	} else {
		hc := http.Client{Timeout: 2}
		switch {
		case attackParser.Invoked:
			requestMap := make(map[string]string)
			requestMap["sender"] = "false"
			requestMap["meeting_id"] = "test"
			requestMap["bbb_server_uri"] = config.BBBServerUri
			requestMap["bbb_secret"] = config.BBBSecret

			checksum := gorcp.GetChecksum(&requestMap, "startBot", rcpConfig)
			requestMap["checksum"] = checksum
			if requestBody, err := json.Marshal(requestMap); err != nil {
				fmt.Println(err.Error())
				os.Exit(1)
			} else {
				for _, centuria := range config.CenturiaUris {
					hc.Post(centuria+"/api/v1/startBot", "application/json", bytes.NewReader(requestBody))
				}
			}

		case withdrawParser.Invoked:
		}
	}
}
