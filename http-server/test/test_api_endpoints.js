const assert = require('assert');
const request = require('supertest');
const { get } = require('../routes/users');

const server = require('../server');

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

