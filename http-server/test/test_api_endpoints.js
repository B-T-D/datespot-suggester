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

