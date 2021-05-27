/* Plan 5/27: This is the Node RESTful HTTP server. It will communicate with the db/model layer
implemented in Python scripts via linux FIFO pipes. */

const fs = require("fs");
const { spawn, fork } = require("child_process");

const IPC_FIFO_NAME_A = "ponche_a"
const IPC_FIFO_NAME_B = "ponche_b"

let fifo_b = spawn("mkfifo", [IPC_FIFO_NAME_B]); 

// TODO TBC, see the rest of the example

