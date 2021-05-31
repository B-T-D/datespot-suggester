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

function queryDb(queryData) {
    return new Promise((resolve, reject) => {

        console.log('---------------------------');
        console.log(`quryDB called, data = ${JSON.stringify(queryData)}`);
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
            resolve(responseData)
        }).on('error', (error) => {
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
        // dbResponse.on('readable', () => {
        //     console.log(`emitted on readable event`);
        //     let data;
        //     while (data = dbResponse.read()) {
        //         responseData += data;
        //     }
        //     responseData = JSON.parse(responseData);
        //     console.log(`dbResponse stream .isPaused() = ${dbResponse.isPaused()}`)
        //     console.log(`dbResponse stream .readableFlowing = ${dbResponse.readableFlowing}`)
        //     console.log(`dbResponse stream .readableEnded = ${dbResponse.readableEnded}`)
        //     console.log(`calling stream.resume()`)
        //     dbResponse.pause();
        //     console.log(`dbResponse stream .isPaused() = ${dbResponse.isPaused()}`)
        //     console.log(`dbResponse stream .readableFlowing = ${dbResponse.readableFlowing}`)
        //     console.log(`dbResponse stream .readableEnded = ${dbResponse.readableEnded}`)
        // })

    })
}

// function transmitViaPipe(requestData) {
//     const fd = fs.openSync(path_b, 'r+');
//     let fifoReadStream = fs.createReadStream(null, { fd });
//     let fifoWriteStream = fs.createWriteStream(path_a);
//     console.log('Node process created writeStream');
//     fifoWriteStream.write(JSON.stringify(requestData));

//     const handleResolve = (resolvedValue) => {
//         console.log(`resolvedValue = ${JSON.stringify(resolvedValue)}`);
//         return resolvedValue
//     }

//     const handleReject = (rejectionReason) => {
//         console.log(`rejected`);
//         let dbRequestError = new Error("Bad request to DB server");
//         return dbRequestError;
//         // return dbRequestError.message;
//     }

//     return new Promise((resolve, reject) => {
//         fifoReadStream.on('data', (data) => {
//             console.log(`received from python: ${data.toString()}`);
//             var responseJSON = data.toString();
//             responseJSON = JSON.parse(responseJSON);
//             if ('error' in responseJSON) {
//                 console.log("found 'error' in response");
//                 let dbRequestError = new Error('UTIL VERSIONBad request to DB server');
//                 reject(dbRequestError)
//             } else {
//                 console.log(`resolving`);
//                 resolve(responseJSON)
//             }
//         })
//     }).then(handleResolve, handleReject)
// }        

// const finished = util.promisify(stream.finished);
// var fd = fs.openSync(path_b, 'r+');

// let writeStream = fs.createWriteStream(path_a);

// readStream.on('end', () => {
//     console.log(`end event emitted`);
// })

// const databaseResponse = new Promise((resolve, reject) => { // Promise that won't resolve until data is written to the readstream, or it times out
//     // readStream.resume();
//     let readStream = fs.createReadStream(null, { fd });
//     readStream.on('data', (data) => {
//         let dbResponse = data.toString()
//         dbResponse = JSON.parse(dbResponse);
//         // readStream.pause()
//         console.log(`dbResponse = ${JSON.stringify(dbResponse)}`);
//         console.log(`next line ran`);
        
//         if ('error' in dbResponse) {
//             let dbRequestError = new Error('Bad request to database');
//             reject(dbRequestError)
//         } else {
//             console.log(`resolve block is running`); // TODO code runs intuitively / as expected at least up to here; setting timeout here did not fix it
//             resolve(dbResponse) // TODO the promise seems to just not be resolving
//         }
//     })
    
// })

// async function databaseRequest(requestData) {
//     //console.log(`readable length is ${readStream.readableLength}`);
    
//     let dbResponse = null; // TODO the issue is not that this namespace has dbRequest and that object has the wrong value; issue is that the request is never defined here; await never ends
//     try {
//         //console.log(`final request data was ${JSON.stringify(requestData)}`);
//         writeStream.write(JSON.stringify(requestData));
//         // await data to be in the pipe
//         return databaseResponse; // TODO this is same as all the unreached code below
//         //return Promise.resolve(databaseResponse); // TODO didn't change anything wrt "stuck" data
//         dbResponse = await databaseResponse; // Nothing to pass here; the writeStream.write call sent the request to the DB
//         console.log(`databaseRequest has dbResponse: ${JSON.stringify(dbResponse)}`)
//         // await finished(readStream); // TODO this never resolves...
//         //readStream.resume(); // drain the stream
//         return dbResponse;
//     } catch(err) {
//         console.log(err);
//     }
// }

module.exports = queryDb;
//module.exports = databaseRequest;