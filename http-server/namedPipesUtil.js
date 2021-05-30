/* TODO rename it to "DB something...", it's more than a util unless there's a further middleman between
this and the express routers */


const fs = require('fs');
const { spawn } = require('child_process');
const { response } = require('express');

const path_a = 'fifo_node_to_python';
const path_b = 'fifo_python_to_node';

const MOCK_CANDIDATE_JSON = {
    "name": "Boethiah",
    "distance": "some distance"
}

const MOCK_REQUEST_JSON = {
    "method": "get_next_candidate",
    "json_arg": {
        "user_id": "1"
    }
}

let responseData = null; /* TODO this seems super ugly (setting this global and then having a while loop wait for it to not be null),
would be better to at least make it a class; best practice is prob to use async stuff */

let pipeIn = spawn('mkfifo', [path_b]);
pipeIn.on('exit', () => {
    console.log('Created Node inbound pipe (DB->Web)'); 
})

function readFromPipe() {
    console.log(`readFromPipe was called`)
    
    let response = null;
    
    
    while (!response) {
        readFromPipe();
    }
    console.log(`got a response = ${response}`);
    return response;

}

function transmitViaPipe(requestData) {
    const fd = fs.openSync(path_b, 'r+');
    let fifoReadStream = fs.createReadStream(null, { fd });
    let fifoWriteStream = fs.createWriteStream(path_a);
    console.log('Node process created writeStream');
    fifoWriteStream.write(JSON.stringify(requestData));

    const handleResolve = (resolvedValue) => {
        console.log(`resolvedValue = ${JSON.stringify(resolvedValue)}`);
        return resolvedValue
    }

    const handleReject = (rejectionReason) => {
        console.log(`rejected`);
        let dbRequestError = new Error("Bad request to DB server");
        return dbRequestError;
        // return dbRequestError.message;
    }

    return new Promise((resolve, reject) => {
        fifoReadStream.on('data', (data) => {
            console.log(`received from python: ${data.toString()}`);
            var responseJSON = data.toString();
            responseJSON = JSON.parse(responseJSON);
            if ('error' in responseJSON) {
                console.log("found 'error' in response");
                let dbRequestError = new Error('UTIL VERSIONBad request to DB server');
                reject(dbRequestError)
            } else {
                console.log(`resolving`);
                resolve(responseJSON)
            }
        })
    }).then(handleResolve, handleReject)
}        

/**
 * 
 * @param {object} requestData : JS object parseable by the database layer interface
 * @returns {object} : JS object for use in HTTP response JSON body
 */
async function databaseRequest(requestData) {

    console.log(`databaseRequest() function called with requestData = ${JSON.stringify(requestData)}`);
    let response = await transmitViaPipe(requestData);
    console.log(`in databaseRequest(): response = ${JSON.stringify(response)}`)
    return response;
    
}

module.exports = databaseRequest;