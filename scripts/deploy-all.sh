#!/bin/bash
# Usage:
#   ./deploy-all.sh              — deploy all workflows
#   ./deploy-all.sh <filename>   — deploy one workflow by filename (e.g. "Auth_ Login with Cookie.json")
set -e

N8N_HOST=$(grep N8N_HOST ../.env | cut -d= -f2 | tr -d '[:space:]' | sed 's|/$||')
N8N_API_KEY=$(grep N8N_API_KEY ../.env | cut -d= -f2 | tr -d '[:space:]')

deploy() {
  local file="$1"
  local id="$2"
  node -e "const fs=require('fs'); const wf=JSON.parse(fs.readFileSync('../workflows/${file}','utf8')); const p={name:wf.name,nodes:wf.nodes,connections:wf.connections,settings:{executionOrder:wf.settings?.executionOrder||'v1'}}; fs.writeFileSync('/tmp/wf_payload.json',JSON.stringify(p));"
  HTTP=$(curl -s -o /tmp/wf_resp.json -w "%{http_code}" -X PUT "${N8N_HOST}/api/v1/workflows/${id}" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" -H "Content-Type: application/json" -d @/tmp/wf_payload.json)
  if [ "$HTTP" = "200" ]; then
    ACT=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${N8N_HOST}/api/v1/workflows/${id}/activate" \
      -H "X-N8N-API-KEY: ${N8N_API_KEY}")
    echo "[OK $HTTP/$ACT] $file"
  else
    ERR=$(cat /tmp/wf_resp.json | head -c 200)
    echo "[ERR $HTTP] $file — $ERR"
  fi
}

FILTER="$1"
maybe_deploy() {
  if [ -z "$FILTER" ] || [ "$FILTER" = "$1" ]; then
    deploy "$1" "$2"
  fi
}

maybe_deploy "Auth Guard (Sub-Workflow).json"           "33ehIaQultvJQW4K"
maybe_deploy "Auth_ Login with Cookie.json"             "9FbRWiFet1FFwyE3"
maybe_deploy "Auth_ Logout.json"                        "SjzUOnqE5szCpYXZ"
maybe_deploy "Auth_ Validate Session.json"              "yLvVeVwQTikzBupE"
maybe_deploy "Notify_ Google Chat (Sub-Workflow).json"  "G2SEoq84kLWf054f"
maybe_deploy "API Key_ Create.json"                     "4vMMf9gEy08vfgqn"
maybe_deploy "API Key_ List.json"                       "H7wJz3BhPSCIms5l"
maybe_deploy "API Key_ Revoke.json"                     "eQaADKqRy8sq6Cwb"
maybe_deploy "Approve BRD.json"                         "bqsFNYeLXd4RgI5P"
maybe_deploy "Approve PRD.json"                         "0RuH9ol8fEacClbG"
maybe_deploy "Cancel Workflow.json"                     "6axRccYtD9yTBhCG"
maybe_deploy "Close Project.json"                       "1JMmZxfpQv1s416Z"
maybe_deploy "Generate BRD.json"                        "s4f9eq0kWQRQQVOZ"
maybe_deploy "Get All Projects.json"                    "iXLY3EzvPUolh8GI"
maybe_deploy "Get Nexus Job Status.json"                "vdH2fP8kR18qgZVF"
maybe_deploy "Get Project Activity.json"                "w74LPJwDB5nHMlBa"
maybe_deploy "Get Project Status.json"                  "hfZHA984R3CJQnqY"
maybe_deploy "Nexus Design-to-Code.json"                "DkXBnhQfdljerHL0"
maybe_deploy "Step 0_ Delete Project Workflow.json"     "d2yKHHcMRbuEnJFYS1Oqx"
maybe_deploy "Step 1_ Project Setup.json"               "53RFGal8I0iGusia"
maybe_deploy "Step 2_ PRD Generation.json"              "a8pewV9pFoYUIVol"
maybe_deploy "Step 3_ Dev Tasks Generation.json"        "TdtLd37Cy1f0uz2d"
maybe_deploy "User Management_ Approve User.json"       "PwuvC76zRDSSf7Dp"
maybe_deploy "User Management_ Delete User.json"        "yHQN2rFzsb3HlJzK"
maybe_deploy "User Management_ Get All Users.json"      "DiTpSOoB4MNtKvq5"
maybe_deploy "User Management_ Invite User.json"        "ZC3ZV3Jc1QpOn7Py"
