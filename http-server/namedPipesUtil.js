
/* Temp mock function to call */

const MOCK_CANDIDATE_JSON = {
    "name": "Boethiah",
    "distance": "some distance"
}

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