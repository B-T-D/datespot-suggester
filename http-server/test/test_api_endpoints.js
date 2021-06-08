const assert = require('assert');
const request = require('supertest');
const { get } = require('../routes/users');

const server = require('../server');

/**
 * Endpoints as of 6/8:
 *  api/v1 [GET]
 *      /candidates
 *          /next [GET]
 *          /decision [POST]
 *      /users
 *          /login/:userId [GET]
 *          /signup [POST]
 *              
 */

describe('API root URL', () => {
    describe('GET request', () => {
        it('returns a 200 status to indicate that the server is online', async () => {
            
            // Exercise
            const response = await request(server)
            .get('/api/v1');

            // Verify
            assert.equal(response.status, 200);

        })
    })
})

describe('Next-candidate URL', () => {
    describe('GET request', () => {
        it('returns status code 200 in response to a properly formed request', async () => {

            const response = await request(server)
            .get('/api/v1/candidates/next?userId=1');

            assert.equal(response.status, 200);
        })
    })
})

// describe('Decision URL', () => {
//     describe('POST request status code', () => {
//         it('Returns status code 200 in response to a properly formed request', async () => {
//             const response = await request(server)
//             .get('/api/v1/candidates/decision?userId=1&&candidateId=5&outcome=true')

//             assert.equal(response.status, 200);
//         })
//     })
// })

