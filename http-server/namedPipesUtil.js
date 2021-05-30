const fs = require('fs');
const { spawn, fork } = require('child_process');


const path_a = 'fifo_node_to_python';
const path_b = 'fifo_python_to_node';

const MOCK_CANDIDATE_JSON = {
    "name": "Boethiah",
    "distance": "some distance"
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
            fifoWriteStream.write(JSON.stringify(MOCK_CANDIDATE_JSON));
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

pipeHelloWorld()

/* Temp mock function to call */



/**
 * Returns JSON according to args.
 * 
 * @param {object} dataIn : JS object parseable by the database layer interface
 * @returns {object} : JS object for use in an HTTP response
 */
function usePipe(dataIn) {
    return mockPipeOutput(dataIn);
}

/* TODO temp simulation of what might come back from the pipes in response to a specifie
input */
function mockPipeOutput(dataIn) {
    if (dataIn["method"] === "get_next_candidate") { // TODO see database_api.py docstrings for what the JSON arg would need to be in a real request to this method
        return MOCK_CANDIDATE_JSON;
    } 
}

module.exports = usePipe;