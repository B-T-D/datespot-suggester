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

    return new Promise((resolve, reject) => {
        fifoReadStream.on('data', (data) => {
            console.log(`received from python: ${data.toString()}`);
            resolve(data.toString())
        })
    })        
    
    
    
    var responseData = null;
    fifoReadStream.on('data', (data) => { // Need this listener in place before the request is written to the pipe, so it'll be there when response comes (?)
        console.log(`received from Python: ${data.toString()}`)
        responseData = data.toString();
        console.log(`responseData is now ${responseData}`);
        // console.log(`resolve line about to run`);
        // resolve(responseData);
        // console.log(`line after resolve line`);
    })
    console.log(`this line ran, response data was ${responseData}`);
    fifoReadStream.on('end', function () {
        console.log(`*****in fiforeadstream.on end: responseData = ${responseData}`)
    })
    
    
}

/**
 * 
 * @param {object} requestData : JS object parseable by the database layer interface
 * @returns {object} : JS object for use in HTTP response JSON body
 */
async function databaseRequest(requestData) {

    console.log(`databaseRequest() function called with requestData = ${JSON.stringify(requestData)}`);
    var response = await transmitViaPipe(requestData)
    console.log(`in databaseRequest(): response = ${response}`)
    return response;
    
}

function pipeHelloWorld() {
    let pipeIn = spawn('mkfifo', [path_b]); // Create the inbound pipe
    console.log(`Node pipeIn = ${pipeIn}`)
    pipeIn.on('exit', () => {
        console.log('Created Node inbound pipe');

        const fd = fs.openSync(path_b, 'r+');
        let fifoReadStream = fs.createReadStream(null, { fd });
        let fifoWriteStream = fs.createWriteStream(path_a);

        console.log('Node process ready to write');

        setInterval(() => {
            console.log('-----   Send packet   -----');
            fifoWriteStream.write(JSON.stringify(MOCK_REQUEST_JSON));
        }, 1000); // Write data at 1 second interval

        fifoReadStream.on('data', data => {
            now_time = new Date();
            sent_time = new Date(data.toString());
            latency = (now_time - sent_time);

            console.log('----- Received packet -----');
            console.log('    Date   : ' + data.toString());
            console.log('    Latency: ' + latency.toString() + ' ms');

        });
    });
}


var mockDataIn = {
    "method": "get_next_candidate",
    "json_arg": {
        "user_id": "1"
    }
}

// var jsonResponse = databaseRequest(mockDataIn)
// console.log(jsonResponse)

module.exports = databaseRequest;
//module.exports = usePipe;