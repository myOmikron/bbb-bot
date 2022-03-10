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
		if len(config.CenturiaUris) == 0 {
			fmt.Println("No centurias available, exiting ...")
			os.Exit(0)
		}
		if config.BBBServerUri == "" {
			fmt.Println("BBB server uri is empty, exiting ...")
			os.Exit(0)
		}
		if config.BBBSecret == "" {
			fmt.Println("BBB secret is empty, exiting ...")
			os.Exit(0)
		}
		if config.RCPSecret == "" {
			fmt.Println("RCP Secret is empty, exiting ...")
			os.Exit(0)
		}
	}

	rcpConfig := &gorcp.RCPConfig{
		UseTimeComponent: true,
		SharedSecret:     config.RCPSecret,
	}

	parser := argparse.NewParser("centurion", "Commander of bbb-bots", nil)

	attackParser := parser.AddCommand("attack", "Start the attack", nil)
	armySize := attackParser.Int("", "armySize", &argparse.Option{Positional: true, Required: true})
	senderCount := attackParser.Int("", "sender-count", &argparse.Option{Default: "2"})

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

			for i := 0; i < *armySize; i++ {
				if i < *senderCount {
					requestMap["sender"] = "true"
				}
				checksum := gorcp.GetChecksum(&requestMap, "startBot", rcpConfig)
				requestMap["checksum"] = checksum
				if requestBody, err := json.Marshal(requestMap); err != nil {
					fmt.Println(err.Error())
					os.Exit(1)
				} else {
					targetIdx := i % len(config.CenturiaUris)
					centuria := config.CenturiaUris[targetIdx]
					if post, err := hc.Post(centuria+"/api/v1/startBot", "application/json", bytes.NewReader(requestBody)); err != nil {
						fmt.Println(err.Error())
						os.Exit(1)
					} else {
						if post.StatusCode != 200 {
							var body []byte
							_, err := post.Body.Read(body)
							if err != nil {
								break
							}
							var res []interface{}
							if err := json.Unmarshal(body, &res); err != nil {
								break
							}
							fmt.Printf("Status: %d: %v\n", post.StatusCode, res)
						}
					}
				}
			}
			fmt.Printf("Spawned %d soldiers in meeting %s\n", *armySize, "test")

		case withdrawParser.Invoked:
		}
	}
}
