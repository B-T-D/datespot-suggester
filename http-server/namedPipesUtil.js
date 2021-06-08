/* TODO rename it to "DB something...", it's more than a util unless there's a further middleman between
this and the express routers */


const fs = require('fs');
const stream = require('stream');
const util = require('util');
const { spawn } = require('child_process');
const { response } = require('express');
const { Readable } = require('stream');

const database_request_named_pipe_path = 'fifo_node_to_python';
const database_response_named_pipe_path = 'fifo_python_to_node';

let pipeIn = spawn('mkfifo', [database_response_named_pipe_path]);
pipeIn.on('exit', () => {
    console.log('Created Node inbound pipe (DB->Web)'); 
})

const fd = fs.openSync(database_response_named_pipe_path, 'r+');
let dbRequest = fs.createWriteStream(database_request_named_pipe_path);
let dbResponse = fs.createReadStream(null, { fd });

/**
 * Returns a JSON string matching the protocol expected by the database server on the other end of the pipe.
 * 
 * @param {Object} queryData 
 * @returns {Object} New object containing a "packet_size" property and the original queryData Object nested as the value of the "body_json" property
 */

function constructDbRequest(queryData) {
    let dbQueryObj = {
        "body_json": queryData
    }

    const sizePlaceholder = 256;

    dbQueryObj["packet_size"] = sizePlaceholder;

    // TODO construct a correct size. https://stackoverflow.com/questions/1248302/how-to-get-the-size-of-a-javascript-object

    return dbQueryObj;
}

/**
 * 
 * @param {Obj} queryData : Body of the DB request, containing the database method to call and the json_arg to pass to that DB method.
 *      Examples:
 *          {"method": "get_next_candidate",
            "json_arg": {"user_id": userId}}
 * @returns {Promise} : Promise that resolves to the JSON string returned by the database server
 */
function queryDb(queryData) {
    return new Promise((resolve, reject) => {

        queryData = constructDbRequest(queryData);

        console.log('---------------------------');
        console.log(`queryDB called, data = ${JSON.stringify(queryData)}`);
        console.log(`dbResponse stream .isPaused() = ${dbResponse.isPaused()}`)
        console.log(`dbResponse stream .readableFlowing = ${dbResponse.readableFlowing}`)
        console.log(`dbResponse stream .readableEnded = ${dbResponse.readableEnded}`)
        console.log('---------------------------');

        dbResponse.on('data', (data) => {
            console.log(`emitted on data event`);
            responseData = JSON.parse(data.toString());
            dbResponse.pause();
            console.log(`dbResponse stream .isPaused() = ${dbResponse.isPaused()}`)
            console.log(`dbResponse stream .readableFlowing = ${dbResponse.readableFlowing}`)
            console.log(`dbResponse stream .readableEnded = ${dbResponse.readableEnded}`)
            console.log(`responseData = ${JSON.stringify(responseData)}`);
        }).on('pause', () => {
            console.log(`emitted pause event`);
            //dbResponse.resume();
            console.log(`attempting to remove all listeners from DB response`);
            dbResponse.resume();
            dbResponse.removeAllListeners();
            resolve(responseData['body_json'])
        }).on('error', (error) => {
            console.log(`emitted error event`);
            reject(error);
        }).on('resume', () => {
            console.log(`emitted resume event`);  
        })
        // dbResponse.on('end', () => {
        //     console.log(`emitted on end event`);
        //     resolve(responseData)
        // })
        dbRequest.write(JSON.stringify(queryData));
        let responseData = '';

    })
}

module.exports = queryDb;